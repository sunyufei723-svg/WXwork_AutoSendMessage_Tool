@echo off
chcp 65001 >nul
rem ============================================

cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 exit /b 1
)
rem 打包脚本：将项目打包为单文件 exe
rem 首次运行会自动创建 venv 并安装依赖
rem ============================================

rem 激活虚拟环境
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

rem 确保 PyInstaller 已安装
python -m pip show pyinstaller >nul 2>nul || python -m pip install pyinstaller
if errorlevel 1 exit /b 1

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
if errorlevel 1 exit /b 1

echo.
echo ============ 打包完成 ============
echo 产物位置: dist\WXwork_AutoSendMessage_Tool.exe
echo 分发时请将 templates\ 文件夹与 exe 放在同一目录
echo 已保存的名单位于程序旁的 rosters\，迁移时请一起复制
pause
