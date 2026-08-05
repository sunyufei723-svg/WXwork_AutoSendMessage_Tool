"""应用全局常量与路径。"""

import os
import sys


def _get_app_dir():
    """获取程序所在目录：打包后为 exe 所在目录，开发时为项目根目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_TITLE = "企业微信群发助手"

# 路径统一基于程序所在目录，保证打包成 exe 后 config/templates 位置正确
APP_DIR = _get_app_dir()
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
TEMPLATE_DIR = os.path.join(APP_DIR, "templates")

SUPPORTED_TEMPLATE_EXTS = (
    ".txt",
    ".md",
    ".template",
)

# ── 颜色常量 ──
BG_MAIN = "#eef2f7"
BG_CARD = "#ffffff"
FG_TITLE = "#1a1a2e"
FG_LABEL = "#333333"
FG_HINT = "#999999"
CLR_SUCCESS = "#28a745"
CLR_DANGER = "#dc3545"
