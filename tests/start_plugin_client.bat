@echo off
REM Start WSS Plugin Client on Windows
REM Usage: start_plugin_client.bat [options]
REM
REM Options:
REM   --remote-host HOST          WSS server host (default: 127.0.0.1)
REM   --remote-port PORT          WSS server port (default: 8443)
REM   --local-host HOST           Local listen host (default: 127.0.0.1)
REM   --local-port PORT           Local listen port (default: 1080)
REM   --cert FILE                 SSL certificate file for verification (optional)
REM   --debug                     Enable debug logging
REM   --log-file FILE             Log file path (optional)
REM
REM Examples:
REM   start_plugin_client.bat
REM   start_plugin_client.bat --remote-host 10.0.0.1 --remote-port 8443
REM   start_plugin_client.bat --debug --log-file client.log

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Set default environment variables
set "SS_REMOTE_HOST=127.0.0.1"
set "SS_REMOTE_PORT=8443"
set "SS_LOCAL_HOST=127.0.0.1"
set "SS_LOCAL_PORT=1080"
set "SS_PLUGIN_OPTIONS="

REM Parse command line arguments
:parse_args
if "%~1"=="" goto args_done
if "%~1"=="--remote-host" (
    set "SS_REMOTE_HOST=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--remote-port" (
    set "SS_REMOTE_PORT=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--local-host" (
    set "SS_LOCAL_HOST=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--local-port" (
    set "SS_LOCAL_PORT=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--cert" (
    set "CERT_FILE=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--debug" (
    set "DEBUG_FLAG=true"
    shift
    goto parse_args
)
if "%~1"=="--log-file" (
    set "LOG_FILE=%~2"
    shift
    shift
    goto parse_args
)
shift
goto parse_args

:args_done
REM Build SS_PLUGIN_OPTIONS with proper semicolon handling
if defined CERT_FILE (
    set "SS_PLUGIN_OPTIONS=cert=!CERT_FILE!"
)
if defined DEBUG_FLAG (
    if defined SS_PLUGIN_OPTIONS (
        set "SS_PLUGIN_OPTIONS=!SS_PLUGIN_OPTIONS!;debug=true"
    ) else (
        set "SS_PLUGIN_OPTIONS=debug=true"
    )
)
if defined LOG_FILE (
    if defined SS_PLUGIN_OPTIONS (
        set "SS_PLUGIN_OPTIONS=!SS_PLUGIN_OPTIONS!;log_file=!LOG_FILE!"
    ) else (
        set "SS_PLUGIN_OPTIONS=log_file=!LOG_FILE!"
    )
)

REM Check if executable exists
if not exist "%SCRIPT_DIR%..\dist\wss-plugin-client\wss-plugin-client.exe" (
    echo Error: wss-plugin-client.exe not found at ..\dist\wss-plugin-client\
    echo Please build the executable first using build_executable.py
    exit /b 1
)

REM Run the executable with environment variables set
echo Starting WSS Plugin Client...
echo.
echo Configuration:
echo   Remote (WSS):    !SS_REMOTE_HOST!:!SS_REMOTE_PORT!
echo   Local (SOCKS):   !SS_LOCAL_HOST!:!SS_LOCAL_PORT!
if defined CERT_FILE echo   Certificate:     !CERT_FILE!
if defined DEBUG_FLAG echo   Debug:           enabled
if defined LOG_FILE echo   Log File:        !LOG_FILE!
echo.

"%SCRIPT_DIR%..\dist\wss-plugin-client\wss-plugin-client.exe"

exit /b %ERRORLEVEL%
