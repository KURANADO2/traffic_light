// Claude Code status light for ESP32-C3 SuperMini.
// Arduino IDE board: ESP32C3 Dev Module.
// USB CDC On Boot: Enabled.

#include <string.h>

const int RED_PIN = 2;
const int YELLOW_PIN = 3;
const int GREEN_PIN = 4;

// The common positive terminal is connected to 3.3V, so LOW turns a lamp on.
const int LIGHT_ON = LOW;
const int LIGHT_OFF = HIGH;

const unsigned long WORKING_BLINK_MS = 600;
const unsigned long WAITING_BLINK_MS = 180;

enum ClaudeState {
  STATE_IDLE,
  STATE_WORKING,
  STATE_WAITING,
  STATE_OFF,
  STATE_TEST
};

ClaudeState currentState = STATE_IDLE;
unsigned long lastBlinkAt = 0;
bool blinkOn = false;

char commandBuffer[32];
size_t commandLength = 0;

void writeLight(int pin, bool on) {
  digitalWrite(pin, on ? LIGHT_ON : LIGHT_OFF);
}

void setLights(bool red, bool yellow, bool green) {
  writeLight(RED_PIN, red);
  writeLight(YELLOW_PIN, yellow);
  writeLight(GREEN_PIN, green);
}

void enterState(ClaudeState newState) {
  currentState = newState;
  lastBlinkAt = millis();
  blinkOn = true;

  switch (currentState) {
    case STATE_IDLE:
      setLights(false, true, false);
      Serial.println("OK idle");
      break;
    case STATE_WORKING:
      setLights(false, false, true);
      Serial.println("OK working");
      break;
    case STATE_WAITING:
      setLights(true, false, false);
      Serial.println("OK waiting");
      break;
    case STATE_OFF:
      setLights(false, false, false);
      Serial.println("OK off");
      break;
    case STATE_TEST:
      setLights(true, false, false);
      Serial.println("OK test");
      break;
  }
}

void printHelp() {
  Serial.println("Commands:");
  Serial.println("  working - blink green while Claude is working");
  Serial.println("  waiting - blink red while Claude needs confirmation");
  Serial.println("  idle    - keep yellow on while Claude is idle");
  Serial.println("  off     - turn all lights off");
  Serial.println("  test    - test red, yellow, and green");
  Serial.println("  status  - print the current state");
}

void printStatus() {
  switch (currentState) {
    case STATE_IDLE:
      Serial.println("STATE idle");
      break;
    case STATE_WORKING:
      Serial.println("STATE working");
      break;
    case STATE_WAITING:
      Serial.println("STATE waiting");
      break;
    case STATE_OFF:
      Serial.println("STATE off");
      break;
    case STATE_TEST:
      Serial.println("STATE test");
      break;
  }
}

void handleCommand(char* command) {
  for (size_t i = 0; command[i] != '\0'; i++) {
    if (command[i] >= 'A' && command[i] <= 'Z') {
      command[i] += 'a' - 'A';
    }
  }

  if (strcmp(command, "working") == 0) {
    enterState(STATE_WORKING);
  } else if (strcmp(command, "waiting") == 0) {
    enterState(STATE_WAITING);
  } else if (strcmp(command, "idle") == 0) {
    enterState(STATE_IDLE);
  } else if (strcmp(command, "off") == 0) {
    enterState(STATE_OFF);
  } else if (strcmp(command, "test") == 0) {
    enterState(STATE_TEST);
  } else if (strcmp(command, "status") == 0) {
    printStatus();
  } else if (strcmp(command, "help") == 0) {
    printHelp();
  } else if (command[0] != '\0') {
    Serial.print("ERROR unknown command: ");
    Serial.println(command);
  }
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    char incoming = Serial.read();

    if (incoming == '\n' || incoming == '\r') {
      if (commandLength > 0) {
        commandBuffer[commandLength] = '\0';
        handleCommand(commandBuffer);
        commandLength = 0;
      }
      continue;
    }

    if (commandLength < sizeof(commandBuffer) - 1) {
      commandBuffer[commandLength++] = incoming;
    } else {
      commandLength = 0;
      Serial.println("ERROR command too long");
    }
  }
}

void updateBlinkingState() {
  unsigned long now = millis();
  unsigned long interval = currentState == STATE_WAITING
                               ? WAITING_BLINK_MS
                               : WORKING_BLINK_MS;

  if (now - lastBlinkAt < interval) {
    return;
  }

  lastBlinkAt = now;
  blinkOn = !blinkOn;

  if (currentState == STATE_WORKING) {
    setLights(false, false, blinkOn);
  } else if (currentState == STATE_WAITING) {
    setLights(blinkOn, false, false);
  }
}

void updateTestState() {
  const unsigned long stepDuration = 700;
  unsigned long step = (millis() - lastBlinkAt) / stepDuration;

  if (step == 0) {
    setLights(true, false, false);
  } else if (step == 1) {
    setLights(false, true, false);
  } else if (step == 2) {
    setLights(false, false, true);
  } else {
    enterState(STATE_IDLE);
  }
}

void setup() {
  pinMode(RED_PIN, OUTPUT);
  pinMode(YELLOW_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  setLights(false, false, false);

  Serial.begin(115200);
  delay(300);

  Serial.println();
  Serial.println("Claude status light ready");
  printHelp();
  enterState(STATE_IDLE);
}

void loop() {
  readSerialCommands();

  if (currentState == STATE_WORKING || currentState == STATE_WAITING) {
    updateBlinkingState();
  } else if (currentState == STATE_TEST) {
    updateTestState();
  }
}
