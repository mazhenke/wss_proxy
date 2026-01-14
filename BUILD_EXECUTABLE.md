# WSS Plugin 可执行文件构建指南

本脚本使用 **PyInstaller** 将 Python 脚本打包成平台相关的可执行文件：
- **Linux**: ELF 格式可执行文件  
- **Windows**: EXE 可执行文件  
- **macOS**: Mach-O 可执行文件

## 安装依赖

```bash
pip install pyinstaller
```

## 使用方法

### 1. 构建客户端（默认）

```bash
python3 build_executable.py --client
```

输出：`dist/wss-plugin-client/wss-plugin-client` (Linux/macOS)  
输出：`dist/wss-plugin-client/wss-plugin-client.exe` (Windows)

### 2. 构建服务端

```bash
python3 build_executable.py --server
```

输出：`dist/wss-plugin-server/wss-plugin-server` (Linux/macOS)  
输出：`dist/wss-plugin-server/wss-plugin-server.exe` (Windows)

### 3. 构建两者

```bash
python3 build_executable.py --all
```

### 4. 生成单一文件（推荐用于分发）

```bash
python3 build_executable.py --all --onefile
```

输出：
- `dist/wss-plugin-client` (单个可执行文件)
- `dist/wss-plugin-server` (单个可执行文件)

### 5. 隐藏控制台窗口（仅 Windows）

```bash
python3 build_executable.py --all --windowed
```

### 6. 自定义输出目录

```bash
python3 build_executable.py --all --output ./executables
```

## 选项说明

| 选项 | 说明 |
|------|------|
| `--client` | 只构建客户端 |
| `--server` | 只构建服务端 |
| `--all` | 构建两者 |
| `--onefile` | 生成单文件可执行文件（默认为文件夹模式） |
| `--output DIR` | 指定输出目录（默认：dist） |
| `--windowed` | 隐藏控制台（仅 Windows） |

## 常见用法示例

### Linux 用户

```bash
# 构建单文件，方便分发
python3 build_executable.py --all --onefile

# 可执行文件会在：
# dist/wss-plugin-client
# dist/wss-plugin-server

# 赋予执行权限
chmod +x dist/wss-*

# 运行
./dist/wss-plugin-client
./dist/wss-plugin-server
```

### Windows 用户

```bash
# 构建单文件 EXE
python3 build_executable.py --all --onefile --windowed

# 输出在：
# dist\wss-plugin-client.exe
# dist\wss-plugin-server.exe

# 双击运行或在 CMD 中执行
wss-plugin-client.exe
wss-plugin-server.exe
```

## 文件夹模式 vs 单文件模式

### 文件夹模式（默认）
- 构建快速
- 启动快速
- 包含依赖文件夹
- 文件夹必须完整分发

### 单文件模式（--onefile）
- 构建较慢
- 启动略慢（首次解压）
- 单个可执行文件
- 方便分发和使用

## 故障排除

### 1. PyInstaller 未安装
```
Error: pyinstaller not found
```

解决：
```bash
pip install pyinstaller
```

### 2. 找不到脚本文件
```
Error: wss_plugin_client.py not found
```

解决：确保在脚本所在目录运行

### 3. 生成的文件无法运行
- 检查依赖库是否完整（特别是 websockets）
- 尝试单文件模式：`--onefile`
- 确保 Python 版本一致

### 4. Windows Defender 警告
自编译的可执行文件可能被 Windows Defender 标记，这是正常的。可：
- 将文件添加到排除名单
- 或上传至 VirusTotal 扫描以排除误报

## 跨平台编译

**重要**：PyInstaller 编译的文件是平台相关的：
- 在 Linux 上编译 → Linux 可执行文件
- 在 Windows 上编译 → Windows 可执行文件
- 在 macOS 上编译 → macOS 可执行文件

要生成多平台版本，需在各自平台上编译。

### CI/CD 跨平台编译示例（GitHub Actions）

```yaml
name: Build Executables

on: [push, pull_request]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: pip install pyinstaller websockets
    
    - name: Build executables
      run: python3 build_executable.py --all --onefile
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: executables-${{ matrix.os }}
        path: dist/
```

## 性能和大小

生成的可执行文件大小通常 30-80 MB（取决于平台和依赖）

如需减小大小，可使用 UPX 压缩：

```bash
pip install pyinstaller[hook-contrib]
pyinstaller ... --upx-dir=/path/to/upx ...
```

## 更多信息

- PyInstaller 官方文档：https://pyinstaller.readthedocs.io/
- WSS Plugin 源码：见 `wss_plugin_client.py` 和 `wss_plugin_server.py`
