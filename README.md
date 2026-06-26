# Claude Code 红绿灯状态提示器

使用 ESP32-C3 SuperMini 改造一个淘宝红绿灯玩具，让 Claude Code 的状态通过红、黄、绿三颗灯显示：

| Claude Code 状态 | 灯光效果 |
|----------------|------|
| 正在工作 | 绿灯慢闪 |
| 等待用户确认、授权或选择 | 红灯快闪 |
| 当前空闲 | 黄灯常亮 |
| 会话结束 | 全部熄灭 |

## 硬件

- ESP32-C3 SuperMini 开发板
  - https://item.taobao.com/item.htm?id=811309798924&mi_id=0000q_uHS1EjAgYjvSh61QaMD7pTWOa9WYaP1ematy-Un-E&spm=tbpc.boughtlist.suborder_itemtitle.1.39ba2e8d3ISAjA&skuId=5675158659269
  - https://www.nologo.tech/product/esp32/esp32c3/esp32c3supermini/esp32C3SuperMini.html
- 淘宝红绿灯主体
  - https://item.taobao.com/item.htm?id=1042775053026&mi_id=0000GmG6P7jSSweQo17Zt9fSNmjajelDsquU54hyNl7JBT8&spm=tbpc.boughtlist.suborder_itempic.d1042775053026.4bb42e8deacO41&skuId=6228536371178
- 220 欧电阻 3 个
- 细导线若干
- 焊接工具：电烙铁、焊锡丝、助焊松香、尖嘴钳、电风扇或其他排烟设备

不要同时安装纽扣电池并接入 ESP32 USB 供电。改造后由 ESP32 的 `3V3` 供电。

## 接线定义

红绿灯电路板上的灯位定义如下：

| 灯位 | 颜色 | ESP32-C3 SuperMini 引脚 | 串联电阻 |
|------|------|-------------------------|----------|
| 公共阳极 | 三灯公共正极 | `3V3` | 不需要 |
| `L1` 负极 | 绿灯 | `GPIO4` | `220Ω` |
| `L2` 负极 | 黄灯 | `GPIO3` | `220Ω` |
| `L3` 负极 | 红灯 | `GPIO2` | `220Ω` |

接线关系：

```text
ESP32 3V3 -> 红绿灯公共阳极

绿灯 L1 负极 -> 220Ω -> ESP32 GPIO4
黄灯 L2 负极 -> 220Ω -> ESP32 GPIO3
红灯 L3 负极 -> 220Ω -> ESP32 GPIO2
```

固件使用共阳极控制方式：GPIO 输出 `LOW` 时点亮，输出 `HIGH` 时熄灭。

## 烧录固件

Arduino 程序位于：

```text
arduino/traffic_light_test/traffic_light_test.ino
```

Arduino IDE 设置：

- Board: `ESP32C3 Dev Module`
- USB CDC On Boot: `Enabled`
- Port: 选择 ESP32 对应串口
- 波特率：`115200`

烧录后，打开串口监视器，行结束符选择 `Newline` 或 `Both NL & CR`，可以发送以下命令测试：

| 串口命令 | 灯光效果 |
|----------|------|
| `working` | 绿灯慢闪 |
| `waiting` | 红灯快闪 |
| `idle` | 黄灯常亮 |
| `off` | 全部熄灭 |
| `test` | 红、黄、绿依次点亮 |
| `status` | 输出当前状态 |

## 制作过程

### 1. 红绿灯主体

淘宝买来的红绿灯主体。

![红绿灯主体](img/1-%E7%BA%A2%E7%BB%BF%E7%81%AF%E4%B8%BB%E4%BD%93.jpeg)

### 2. 面包板测试

先烧录程序，在面包板上测试 ESP32 能否通过串口命令监听 Claude Code 状态，并正确控制红、黄、绿三颗灯。

![面包板测试](img/2-%E9%9D%A2%E5%8C%85%E6%9D%BF%E6%B5%8B%E8%AF%95.gif)

[查看高清 MP4](img/2-%E9%9D%A2%E5%8C%85%E6%9D%BF%E6%B5%8B%E8%AF%95.mp4)

### 3. 准备焊接工具

准备电烙铁、焊锡丝、助焊松香、细导线、220 欧电阻、尖嘴钳，以及电风扇排烟。焊接烟雾有害，建议在通风环境下操作。

焊锡丝建议使用含锡量 `>= 63%` 的产品，比较容易上锡。

![焊接前工具准备](img/3-%E7%84%8A%E6%8E%A5%E5%89%8D%E5%B7%A5%E5%85%B7%E5%87%86%E5%A4%87.jpeg)

### 4. 处理较小的焊点

电路板上发光二极管负极焊点比较小，不方便直接焊接。可以用刀小心刮开一点绿油，露出下方铜箔，形成更大的焊接区域。

刮绿油前：

![刮绿油前](img/4-%E7%BA%A2%E7%BB%BF%E7%81%AF%E7%94%B5%E8%B7%AF%E6%9D%BF%E5%88%AE%E6%8E%89%E7%BB%BF%E6%B2%B9%E5%89%8D.jpeg)

刮绿油后：

![刮绿油后](img/4-%E7%BA%A2%E7%BB%BF%E7%81%AF%E7%94%B5%E8%B7%AF%E6%9D%BF%E5%88%AE%E6%8E%89%E7%BB%BF%E6%B2%B9%E5%90%8E.png)

### 5. 焊接红绿灯电路板

分别焊接公共阳极、`L1` 负极、`L2` 负极、`L3` 负极：

- `L1` 是绿灯。
- `L2` 是黄灯。
- `L3` 是红灯。
- `L1`、`L2`、`L3` 负极出来的导线都需要串联 `220Ω` 电阻。

推荐每种灯使用对应颜色的导线，后续排查会更直观。图中 `L1` 绿灯用了红色线、`L3` 红灯用了绿色线，这是个人焊接失误

另外也可以考虑使用贴片电阻，但操作难度更高，这里使用的是普通直插电阻。

![红绿灯焊接](img/5-%E7%BA%A2%E7%BB%BF%E7%81%AF%E7%84%8A%E6%8E%A5.jpeg)

### 6. 剪掉开发板排针

排针太长，为了能够将开发板贴合在红绿灯外壳背后，需要剪掉 ESP32-C3 SuperMini 的排针。

![剪掉排针](img/6-%E5%89%AA%E6%8E%89%E6%8E%92%E9%92%88.jpeg)

### 7. 穿线并固定开发板

用电钻在红绿灯后壳开一个小孔，将导线穿过去，然后用绝缘胶带固定开发板。

![穿线并固定开发板](img/7-%E7%BC%A0%E4%B8%8A%E7%BB%9D%E7%BC%98%E8%83%B6%E5%B8%A6%E5%9B%BA%E5%AE%9A%E5%BC%80%E5%8F%91%E6%9D%BF.jpeg)

### 8. 焊接开发板引脚

开发板侧按以下方式焊接：

| ESP32-C3 SuperMini 引脚 | 连接 |
|-------------------------|------|
| `3V3` | 红绿灯公共阳极 |
| `GPIO4` | `L1` 绿灯负极，串联 `220Ω` |
| `GPIO3` | `L2` 黄灯负极，串联 `220Ω` |
| `GPIO2` | `L3` 红灯负极，串联 `220Ω` |

![开发板引脚焊接](img/8-%E5%BC%80%E5%8F%91%E7%89%88%E5%BC%95%E8%84%9A%E7%84%8A%E6%8E%A5.jpeg)

### 9. 绝缘和固定

缠上绝缘胶带，进一步固定开发板，避免焊点和外壳、其他导线短路。

![绝缘胶带固定](img/9-%E7%BC%A0%E4%B8%8A%E7%BB%9D%E7%BC%98%E8%83%B6%E5%B8%A6%E5%9B%BA%E5%AE%9A.jpeg)

### 10. 最终效果

使用数据线连接电脑和红绿灯，Claude Code 状态会自动反映到灯光上。

![最终效果](img/10-%E6%9C%80%E7%BB%88%E6%95%88%E6%9E%9C.gif)

[查看高清 MP4](img/10-%E6%9C%80%E7%BB%88%E6%95%88%E6%9E%9C.mp4)

## 连接 Claude Code

电脑端桥接脚本位于：

```text
scripts/claude_traffic_light.py
```

它会自动查找 `/dev/cu.usbmodem*`，常驻持有 ESP32 串口，并接收 Claude Code Hooks 发送的状态。脚本只使用 Python 标准库，不需要安装第三方依赖。

手动测试：

```bash
python3 scripts/claude_traffic_light.py working
python3 scripts/claude_traffic_light.py waiting
python3 scripts/claude_traffic_light.py idle
```

如果电脑连接了多个 `/dev/cu.usbmodem*` 设备，可以显式指定 ESP32 串口：

```bash
export CLAUDE_TRAFFIC_LIGHT_PORT=/dev/cu.usbmodem11301
python3 scripts/claude_traffic_light.py working
```

安装 Claude Code Hooks：

```bash
python3 scripts/install_claude_hooks.py
```

安装脚本会读取 `claude-hooks.example.json`，合并到 `~/.claude/settings.json`，并在同目录生成备份：

```text
~/.claude/settings.json.traffic-light-backup
```

Hook 与灯光的主要映射：

| Claude Code 事件 | 发送状态 | 灯光 |
|----------------|---------|------|
| `UserPromptSubmit` | `working` | 绿灯慢闪 |
| `PermissionRequest` | `waiting` | 红灯快闪 |
| `PreToolUse(AskUserQuestion)` | `waiting` | 红灯快闪 |
| `Elicitation` | `waiting` | 红灯快闪 |
| `PostToolUse` | `working` | 绿灯慢闪 |
| `Stop` | `idle` | 黄灯常亮 |
| `SessionEnd` | `off` | 全部熄灭 |

运行桥接脚本或 Claude Code 时，应关闭 Arduino IDE 串口监视器，避免两个程序同时占用 ESP32 串口。

诊断日志位于：

```text
/tmp/claude-traffic-light-<uid>.log
```

## 注意事项

- 焊接前务必断开 USB，并取下原来的纽扣电池。
- 每颗灯的负极需要串联 `220Ω` 电阻，不要让 GPIO 直接短接 LED。
- 焊接后建议用万用表蜂鸣档确认没有短路，再连接电脑。
- 如果灯不响应，先用 Arduino 串口监视器发送 `test`，确认固件和焊接都正常，再检查 Python 脚本和 Claude Hook。
