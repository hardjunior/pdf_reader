@echo off
chcp 65001 >nul
echo ========================================================
echo   Registrando Leitor de PDF no Windows...
echo ========================================================
reg import "%~dp0registrar_leitor.reg"
if %errorlevel% equ 0 (
    echo.
    echo [OK] Aplicativo registrado com sucesso no Windows!
    echo.
    echo Abrindo as configuracoes de Aplicativos Padrao do Windows...
    start ms-settings:defaultapps
) else (
    echo.
    echo [ERRO] Ocorreu uma falha ao registrar as chaves.
)
pause
