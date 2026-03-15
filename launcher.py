"""Windows 打包入口：启动服务并打开浏览器。"""

import threading
import time
import webbrowser

from main import run_server
from src.config import WEB_PORT

URL = f"http://127.0.0.1:{WEB_PORT}"


def open_browser() -> None:
    """延迟打开默认浏览器。"""
    time.sleep(1.5)
    webbrowser.open(URL)


def main() -> None:
    """启动本地应用。"""
    print(f"MieMie Helper starting on {URL}")
    print("Press Ctrl+C to stop")
    threading.Thread(target=open_browser, daemon=True).start()
    run_server(host="127.0.0.1")


if __name__ == "__main__":
    main()
