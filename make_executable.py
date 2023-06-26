import subprocess

subprocess.call(['venv\Scripts\pyinstaller.exe', '--onefile', 'src/updater/update.py'])