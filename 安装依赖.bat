@echo off
chcp 65001 >nul
echo 正在安装项目依赖 (cryptography, ttkbootstrap)...
python -m pip install cryptography ttkbootstrap
if %ERRORLEVEL% EQU 0 (
    echo [成功] 依赖安装完毕。
) else (
    echo [失败] 安装出错，请检查 Python 是否已加入环境变量。
)
pause
