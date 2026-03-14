# Startup Fix And One-Click Launcher

## Goal

- 修复当前启动失败问题
- 提供一个稳定的一条命令入口
- 提供一个 macOS 双击即可启动的脚本入口

## Impact

- Python 依赖声明会补齐实际运行所需模块
- `start.py` 会更稳地准备运行环境后再启动应用
- 仓库根目录会新增一个适合 macOS 的一键启动脚本

## Files

- `pyproject.toml`
- `uv.lock`
- `start.py`
- `start.command`

## Risks

- 启动前自动同步依赖会让启动时间略增
- 如果本地没有 Python / uv / Node.js，启动脚本仍会失败，但会更早暴露问题

## Verification

```bash
uv sync
python3 start.py
curl -I http://localhost:4001
```

## Done Criteria

- `python3 start.py` 能启动应用
- `http://localhost:4001` 返回成功响应
- 仓库中存在可双击的 `start.command`
