@echo off
chcp 65001 >nul
rem ============================================
rem 打包脚本：将项目打包为单文件 exe
rem 首次运行会自动创建 venv 并安装依赖
rem ============================================

rem 激活虚拟环境
call .venv\Scripts\activate.bat

rem 确保 PyInstaller 已安装
pip show pyinstaller >nul 2>nul || pip install pyinstaller

rem 使用 venv 中的 Python 打包，仅排除全局环境中的大型无关第三方库
rem 注意：不要排除标准库模块（如 difflib/unittest 等），否则运行时会报错
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "WXwork_AutoSendMessage_Tool" ^
    --exclude-module cv2 ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module scipy ^
    --exclude-module matplotlib ^
    --exclude-module pytest ^
    main.py

echo.
echo ============ 打包完成 ============
echo 产物位置: dist\WeComBulkSendAssistant.exe
echo 分发时请将 config.json 和 templates\ 文件夹与 exe 放在同一目录
pause
