@echo off
setlocal

set "TOOL_DIR=%~dp0"

if "%~1"=="" (
  echo Drop a Markdown folder onto this file.
  echo.
  echo Example target:
  echo   D:\docs\project-markdown
  echo.
  pause
  exit /b 1
)

set "TARGET=%~1"

if not exist "%TARGET%" (
  echo Target not found:
  echo   %TARGET%
  pause
  exit /b 1
)

if exist "%TARGET%\*" (
  set "DOC_DIR=%TARGET%"
) else (
  set "DOC_DIR=%~dp1"
)

echo DocMemory vector sync
echo Target:
echo   %DOC_DIR%
echo.

pushd "%TOOL_DIR%"
uv run --extra vector docmemory sync "%DOC_DIR%" --vector
set "RC=%ERRORLEVEL%"
popd

echo.
if not "%RC%"=="0" (
  echo Failed with exit code %RC%.
) else (
  echo Done.
)
pause
exit /b %RC%
