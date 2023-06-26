import subprocess

subprocess.call(['venv\Scripts\pyinstaller.exe', '--onefile', 'src/updater/update.py'])
subprocess.call(['python', '-m', 'nuitka', 'src\updater\update.py', '--onefile'])