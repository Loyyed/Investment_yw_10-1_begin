@echo off
cd /d "%~dp0"
set "IPYTHONDIR=%~dp0config\.ipython"
set "JUPYTER_CONFIG_DIR=%~dp0config\.jupyter"
set "JUPYTER_RUNTIME_DIR=%~dp0config\.jupyter-runtime"
"D:/Anaconda/python.exe" -m jupyter lab research.ipynb
