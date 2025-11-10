# XHtrace - 增强版Python Traceroute实现

## 项目简介

XHtrace 是一个功能强大的网络路径追踪工具，提供高性能的 traceroute 引擎，支持 IPv4/IPv6 协议、跨平台兼容性、错误处理机制和全面的测试支持。本实现参考了 NextTrace/NTrace-V1 项目的设计理念，同时提供了更灵活的 API 和更完善的功能支持。

## 主要功能

- **核心 Traceroute 引擎**：提供高性能、跨平台的网络路径追踪
- **双协议栈支持**：完整支持 IPv4 和 IPv6 协议
- **多协议实现**：支持 ICMP 和 UDP 协议的 traceroute 方法
- **跨平台兼容**：在 Windows、macOS 和 Linux 上均能正常工作
- **增强错误处理**：提供完善的错误检测和异常处理机制
- **路由循环检测**：自动识别和报告网络路由循环
- **全面测试套件**：包含多个全球目标的测试用例，确保实现的可靠性
- **结构化 API**：提供灵活易用的 Python API，便于集成到其他项目中

## 安装说明

### 环境要求

- Python 3.6 或更高版本
- 无需额外的 GUI 依赖，专注于核心功能

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用方法

```python
from traceroute import traceroute

# 基本用法
for hop_info, progress, is_destination in traceroute("8.8.8.8"):
    print(f"跳 {hop_info['hop']}: {hop_info.get('ip', '*')} {hop_info.get('hostname', '')}")
    if is_destination:
        break

# 高级配置
results = traceroute(
    target="example.com",
    max_hops=30,
    timeout=2.0,
    packet_size=64,
    protocol="udp",  # 或 "icmp"
    resolve_dns=True,
    max_retries=3,
    debug_mode=False,
    ipv6=False  # 设置为 True 以优先使用 IPv6
)

# 运行测试套件
# python test_traceroute.py

## API 文档

### 主要函数：traceroute

```python
def traceroute(
    target: str,
    max_hops: int = DEFAULT_MAX_HOPS,
    timeout: float = DEFAULT_TIMEOUT,
    packet_size: int = DEFAULT_PACKET_SIZE,
    protocol: str = DEFAULT_PROTOCOL,
    resolve_dns: bool = True,
    max_retries: int = DEFAULT_MAX_RETRIES,
    debug_mode: bool = False,
    ipv6: bool = False
) -> Generator[Tuple[Dict[str, Any], float, bool], None, None]
```

**参数说明**：
- `target`：目标 IP 地址或域名
- `max_hops`：最大跳数限制
- `timeout`：每个数据包的超时时间（秒）
- `packet_size`：数据包大小（字节）
- `protocol`：使用的协议，可选 "icmp" 或 "udp"
- `resolve_dns`：是否解析 IP 到主机名
- `max_retries`：每个跳数的最大重试次数
- `debug_mode`：是否启用调试输出
- `ipv6`：是否优先使用 IPv6

**返回值**：
生成器，每次产生一个元组 `(hop_info, progress, is_destination)`：
- `hop_info`：包含跳数信息的字典
- `progress`：当前进度百分比
- `is_destination`：是否到达目标

## 打包为可执行文件

使用 PyInstaller 可以将程序打包为单个可执行文件：

1. 安装 PyInstaller：
   ```bash
   pip install pyinstaller
   ```

2. 使用提供的 spec 文件打包：
   ```bash
   pyinstaller xhtrace.spec
   ```

3. 打包后的文件将位于 `dist` 目录中

### 注意事项

- 打包前请确保所有依赖已正确安装
- 如需添加应用图标，请将 ico 文件放置在项目根目录，并修改 spec 文件中的 icon 参数
- 如需包含 MaxMind 数据库，请将数据库文件放置在 geoip 目录中

## 使用指南

1. **基本追踪**：
   - 在目标输入框中输入 IP 地址或域名
   - 点击「开始」按钮执行追踪

2. **高级设置**：
   - 选择 IP 版本（IPv4/IPv6）
   - 可以选择追踪协议（ICMP/TCP/UDP）
   - 设置最大跳数、数据包大小和超时时间
   - 启用持续追踪或 MTR 模式

3. **IPv6 使用注意事项**：
   - 使用 IPv6 功能需要您的网络环境支持 IPv6 协议
   - 可以使用 `::1`（IPv6 回环地址）进行本地测试
   - 在某些操作系统上，发送 ICMPv6 数据包可能需要管理员/root 权限
   - 确保防火墙没有阻止 ICMPv6 和 UDPv6 数据包

3. **查看结果**：
   - 表格结果：显示详细的跳数信息
   - 原始输出：显示追踪命令的原始输出
   - 可视化：图形化展示网络路径和延迟统计

4. **导出功能**：
   - 在可视化标签页中可以导出结果或截图
   - 支持多种导出格式

## 多语言支持

程序内置简体中文和英文两种语言，可以通过以下方式切换：

1. 在设置对话框中选择语言
2. 在菜单栏的「设置」->「语言」中选择

## 许可证

本项目采用 MIT 许可证。

## 联系与反馈

如有任何问题或建议，请通过 GitHub Issues 提交反馈。
