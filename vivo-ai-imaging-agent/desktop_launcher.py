"""
小V影像助手 - 桌面启动器

双击此文件即可启动：
1. FastAPI 后端服务 (端口 8000)
2. 自动打开浏览器访问聊天界面

依赖: pip install fastapi uvicorn python-multipart
"""

import subprocess
import webbrowser
import time
import sys
import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SERVER_SCRIPT = os.path.join(PROJECT_ROOT, "server", "api_server.py")
PORT = 8000
URL = f"http://127.0.0.1:{PORT}"


def main():
    print("=" * 55)
    print("  小V影像助手 v2.0 - 桌面启动器")
    print("=" * 55)
    print()
    print(f"  项目目录: {PROJECT_ROOT}")
    print(f"  启动服务器: {SERVER_SCRIPT}")
    print()

    # 检查 server 文件
    if not os.path.exists(SERVER_SCRIPT):
        print("❌ 找不到 server/api_server.py！")
        print("   请确保在项目根目录下运行此脚本。")
        input("\n按 Enter 退出...")
        sys.exit(1)

    # 启动 FastAPI 服务器
    print("🔧 正在启动后端服务...")
    server_process = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # 等待服务器就绪
    print("⏳ 等待服务器就绪...")
    import urllib.request
    for i in range(30):
        time.sleep(0.5)
        try:
            urllib.request.urlopen(f"{URL}/health", timeout=2)
            print(f"✅ 服务器已就绪: {URL}")
            break
        except Exception:
            if i == 0:
                print(f"   等待中... (可能需要 5-10 秒)")
    else:
        print("⚠️ 服务器启动超时，请检查是否有错误。")

    # 打开浏览器
    print(f"🌐 正在打开浏览器: {URL}")
    webbrowser.open(URL)

    print()
    print("=" * 55)
    print("  小V影像助手已启动！")
    print(f"  聊天界面: {URL}")
    print(f"  API 文档: {URL}/docs")
    print()
    print("  关闭此窗口将停止服务。")
    print("=" * 55)
    print()

    # 保持运行，转发服务器输出
    try:
        for line in server_process.stdout:
            if line.strip():
                print(f"  [Server] {line.rstrip()}")
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
    finally:
        server_process.terminate()
        server_process.wait()
        print("服务已停止。")


if __name__ == "__main__":
    main()
