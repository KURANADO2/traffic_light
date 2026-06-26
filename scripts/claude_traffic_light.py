#!/usr/bin/env python3
"""Send Claude Code states to the ESP32 traffic light over USB serial."""

from __future__ import annotations

import glob
import fcntl
import json
import os
import socket
import subprocess
import sys
import termios
import time
from pathlib import Path


SOCKET_PATH = Path(f"/tmp/claude-traffic-light-{os.getuid()}.sock")
LOCK_PATH = Path(f"/tmp/claude-traffic-light-{os.getuid()}.lock")
LOG_PATH = Path(f"/tmp/claude-traffic-light-{os.getuid()}.log")
VALID_STATES = {"working", "waiting", "idle", "off", "test", "status"}


def log(message: str) -> None:
    """Append a diagnostic message without writing to Claude Code output."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} {message}\n")
    except OSError:
        pass


def find_serial_port() -> str | None:
    """Return the configured ESP32 port or the first USB modem port."""
    configured_port = os.environ.get("CLAUDE_TRAFFIC_LIGHT_PORT")
    if configured_port:
        return configured_port if os.path.exists(configured_port) else None

    candidates = sorted(glob.glob("/dev/cu.usbmodem*"))
    return candidates[0] if candidates else None


def configure_serial(fd: int) -> None:
    """Configure an open file descriptor for 115200 baud raw serial I/O."""
    attributes = termios.tcgetattr(fd)
    attributes[0] = 0
    attributes[1] = 0
    attributes[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    attributes[3] = 0
    attributes[4] = termios.B115200
    attributes[5] = termios.B115200
    attributes[6][termios.VMIN] = 0
    attributes[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attributes)


def open_serial() -> int | None:
    """Open and configure the ESP32 serial port, returning None if absent."""
    port = find_serial_port()
    if port is None:
        return None

    try:
        fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        configure_serial(fd)
        os.set_blocking(fd, True)
        return fd
    except OSError as error:
        log(f"Failed to open serial port {port}: {error}")
        return None


def write_state(fd: int, state: str) -> bool:
    """Write one newline-delimited state command to the ESP32."""
    try:
        os.write(fd, f"{state}\n".encode("ascii"))
        termios.tcdrain(fd)
        return True
    except OSError:
        return False


def run_daemon() -> None:
    """Own the serial port and accept state updates over a local socket."""
    lock_file = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        log(f"Another daemon owns the lock: {error}")
        lock_file.close()
        return

    try:
        SOCKET_PATH.unlink(missing_ok=True)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(str(SOCKET_PATH))
        SOCKET_PATH.chmod(0o600)
        log("Daemon started")
    except OSError as error:
        log(f"Failed to create local socket: {error}")
        lock_file.close()
        return

    serial_fd: int | None = None
    desired_state = "idle"

    try:
        while True:
            if serial_fd is None:
                serial_fd = open_serial()
                if serial_fd is not None:
                    log(f"Connected to {find_serial_port()}")
                    # Opening a USB serial connection may reset the ESP32.
                    time.sleep(1.0)
                    if not write_state(serial_fd, desired_state):
                        os.close(serial_fd)
                        serial_fd = None

            server.settimeout(1.0)
            try:
                payload = server.recv(64)
            except socket.timeout:
                continue

            state = payload.decode("ascii", errors="ignore").strip().lower()
            if state not in VALID_STATES:
                continue

            desired_state = state
            if serial_fd is not None and not write_state(serial_fd, state):
                os.close(serial_fd)
                serial_fd = None
    finally:
        if serial_fd is not None:
            os.close(serial_fd)
        server.close()
        SOCKET_PATH.unlink(missing_ok=True)
        lock_file.close()


def start_daemon() -> None:
    """Start the bridge daemon without blocking a Claude Code hook."""
    subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "daemon"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def send_state(state: str) -> int:
    """Send a state to the daemon, starting it when necessary."""
    if state not in VALID_STATES:
        print(f"Unknown state: {state}", file=sys.stderr)
        return 2

    for attempt in range(20):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            client.sendto(state.encode("ascii"), str(SOCKET_PATH))
            return 0
        except OSError:
            if attempt == 0:
                start_daemon()
            time.sleep(0.05)
        finally:
            client.close()

    # Missing hardware must never block Claude Code.
    return 0


def state_for_hook(payload: dict[str, object]) -> str | None:
    """Translate a Claude Code hook payload into a traffic-light state."""
    event = payload.get("hook_event_name")

    if event == "SessionStart":
        return "idle"
    if event == "UserPromptSubmit":
        return "working"
    if event == "PermissionRequest":
        return "waiting"
    if event == "PreToolUse":
        tool_name = str(payload.get("tool_name", ""))
        if tool_name == "AskUserQuestion" or tool_name.endswith("__AskUserQuestion"):
            return "waiting"
        return "working"
    if event in {"PostToolUse", "PostToolUseFailure", "ElicitationResult"}:
        return "working"
    if event == "Notification":
        notification_type = payload.get("notification_type")
        if notification_type in {"permission_prompt", "elicitation_dialog"}:
            return "waiting"
        return None
    if event == "Elicitation":
        return "waiting"
    if event == "Stop":
        return "idle"
    if event == "StopFailure":
        return "waiting"
    if event == "SessionEnd":
        return "off"
    return None


def handle_hook() -> int:
    """Read one Claude Code hook payload from stdin and update the light."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    state = state_for_hook(payload)
    return send_state(state) if state is not None else 0


def main() -> int:
    """Run the daemon or send the requested state."""
    if len(sys.argv) != 2:
        commands = "|".join(["hook", *sorted(VALID_STATES)])
        print(f"Usage: {sys.argv[0]} <{commands}>")
        return 2

    if sys.argv[1] == "daemon":
        run_daemon()
        return 0
    if sys.argv[1] == "hook":
        return handle_hook()

    return send_state(sys.argv[1].lower())


if __name__ == "__main__":
    raise SystemExit(main())
