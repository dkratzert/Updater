#  ----------------------------------------------------------------------------
#  "THE BEER-WARE LICENSE" (Revision 42):
#  Daniel Kratzert <dkratzert@gmx.de> wrote this file.  As long as you retain
#  this notice you can do whatever you want with this stuff. If we meet some day,
#  and you think this stuff is worth it, you can buy me a beer in return.
#  ----------------------------------------------------------------------------
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib import request
from urllib.error import HTTPError

"""
return codes:

2: HTTP error 404 (unable to download)
3: can not kill program instance prior to update
4: No command line options supplied
"""


def show_help():
    print('############ Program updater V1 #################')
    print('Command line options:')
    print('-url "URL"  : URL to the installer executable with {} for the version number e.g. \n'
          '              -url "https://xs3-data.uni-freiburg.de/finalcif/FinalCif-setup-x64-v{}.exe"')
    print('-v version  : Version number of the installer executable')
    print('-p name     : Program name')


def get_optionindex(option: str):
    return sys.argv.index(option)


def get_option(option: str = '') -> str:
    if option in sys.argv and get_optionindex(option):
        value = sys.argv[get_optionindex(option) + 1]
        return value
    return ''


def fetch_update() -> None:
    if not any_options_supplied():
        show_help()
        os.system('pause')
        sys.exit(4)
    url = get_option('-url')
    version = get_option('-v')
    program_name = get_option('-p')
    program_path = Path('update-{}.exe'.format(program_name))
    kill_program_instances(program_name)
    if finalcif_is_still_running():
        sys.exit(3)
    with TemporaryDirectory() as tmpdir:
        tmp_dir = Path(tmpdir)
        try:
            fileName, header = request.urlretrieve(url=url.format(version), filename=tmp_dir.joinpath(program_path))
        except HTTPError as e:
            print(e.code)
            print(fileName, '##')
            sys.exit(2)
        run_updater(fileName)
    return None


def kill_program_instances(program_name: str):
    os.system("taskkill /f /im {}.exe 2> nul".format(program_name))


def finalcif_is_still_running():
    return [x for x in os.popen('tasklist').readlines() if 'finalcif' in x.lower()]


def any_options_supplied():
    if len(sys.argv) > 3:
        return True
    else:
        return False


def run_updater(fileName):
    subprocess.call([fileName])
    Path(fileName).unlink()


if __name__ == '__main__':
    fetch_update()
