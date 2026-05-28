@echo off
setlocal DisableDelayedExpansion

if "%WINROS_ROOT%"=="" (
    for %%I in ("%~dp0..") do set "WINROS_ROOT=%%~fI"
)
if "%ROS2_ROOT%"=="" set "ROS2_ROOT=C:\pixi_ws\ros2-windows"
if "%PYTHON38_ROOT%"=="" set "PYTHON38_ROOT=C:\Python38"
if "%OPENSSL11_BIN%"=="" set "OPENSSL11_BIN=C:\pixi_ws\openssl11\Library\bin"
if "%ROS2_DEPS_BIN%"=="" set "ROS2_DEPS_BIN=C:\pixi_ws\ros2-deps\Library\bin"

if not exist "%ROS2_ROOT%\setup.bat" (
    echo ROS 2 setup.bat was not found at "%ROS2_ROOT%\setup.bat".
    exit /b 1
)

set "WINROS_INSTALL=%WINROS_ROOT%\ros2_ws\install"
if not exist "%WINROS_INSTALL%" (
    echo WinROS ROS 2 install directory was not found at "%WINROS_INSTALL%".
    echo Run scripts\build_ros2_ws.ps1 first.
    exit /b 1
)

set "PATH=%OPENSSL11_BIN%;%ROS2_DEPS_BIN%;%PYTHON38_ROOT%\Scripts;%PYTHON38_ROOT%;%PATH%"
call "%ROS2_ROOT%\setup.bat"
if errorlevel 1 exit /b %errorlevel%

set "PATH=%WINROS_INSTALL%\bin;%WINROS_INSTALL%\Scripts;%WINROS_INSTALL%\lib\winros_mujoco;%WINROS_INSTALL%\lib\winros_robot_adapters;%PATH%"
set "AMENT_PREFIX_PATH=%WINROS_INSTALL%;%AMENT_PREFIX_PATH%"
set "CMAKE_PREFIX_PATH=%WINROS_INSTALL%;%CMAKE_PREFIX_PATH%"
set "PYTHONPATH=%WINROS_INSTALL%\Lib\site-packages;%PYTHONPATH%"
set "RMW_IMPLEMENTATION=rmw_fastrtps_cpp"

echo ROS 2 + WinROS workspace active in this cmd session.
echo Try: ros2 pkg list ^| findstr winros

endlocal & (
    set "WINROS_ROOT=%WINROS_ROOT%"
    set "ROS2_ROOT=%ROS2_ROOT%"
    set "PYTHON38_ROOT=%PYTHON38_ROOT%"
    set "OPENSSL11_BIN=%OPENSSL11_BIN%"
    set "ROS2_DEPS_BIN=%ROS2_DEPS_BIN%"
    set "WINROS_INSTALL=%WINROS_INSTALL%"
    set "PATH=%PATH%"
    set "AMENT_PREFIX_PATH=%AMENT_PREFIX_PATH%"
    set "CMAKE_PREFIX_PATH=%CMAKE_PREFIX_PATH%"
    set "PYTHONPATH=%PYTHONPATH%"
    set "RMW_IMPLEMENTATION=%RMW_IMPLEMENTATION%"
)
