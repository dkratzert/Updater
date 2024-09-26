
call venv\scripts\activate

python.exe -m pip install --upgrade pip
pip install -r requirements-devel.txt -U

venv\Scripts\pyinstaller.exe --clean --onefile src/updater/update.py

REM  Alternatively, but virus scanners do not like it:
REM python -m nuitka src\updater\update.py --onefile