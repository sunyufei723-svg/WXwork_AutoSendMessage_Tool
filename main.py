"""
启动器：程序的唯一入口。

开发运行：python main.py
打包 exe ：执行 build.bat（以本文件为 PyInstaller 入口）
"""

from app.ui.main_window import build_main_window


def main():
    root = build_main_window()
    root.mainloop()


if __name__ == "__main__":
    main()
