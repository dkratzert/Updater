#  ----------------------------------------------------------------------------
#  "THE BEER-WARE LICENSE" (Revision 42):
#  Daniel Kratzert <dkratzert@gmx.de> wrote this file.  As long as you retain
#  this notice you can do whatever you want with this stuff. If we meet some day,
#  and you think this stuff is worth it, you can buy me a beer in return.
#  ----------------------------------------------------------------------------
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

import progressbar as progressbar

"""
return codes:
0: regular end
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


def get_options_index(option: str):
    return sys.argv.index(option)


def get_option(option: str = '') -> str:
    if option in sys.argv and get_options_index(option):
        value = sys.argv[get_options_index(option) + 1]
        return value
    return ''


def show_progress(block_num, block_size, total_size):
    pbar = progressbar.ProgressBar(maxval=total_size)
    pbar.start()
    downloaded = block_num * block_size
    if downloaded < total_size:
        pbar.update(downloaded)
    else:
        pbar.finish()


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
    tmp_dir = Path(__file__).parent
    try:
        print('Downloading setup file from:', url.format(version))
        file_name, header = request.urlretrieve(url=url.format(version), filename=tmp_dir.joinpath(program_path),
                                                reporthook=show_progress)
    except HTTPError as e:
        check_for_404_error(e)
        return None
    if is_checksum_valid(file_name, url.format(version)):
        print('Checksum OK')
        run_updater(file_name)
    else:
        print('Checksum Failed. Aborting update!')
        return None
    return None


def is_checksum_valid(setupfile, sha_url):
    # download SHA file:
    sha_url = str(sha_url)[:-4] + '-sha512.sha'
    print('Downloading sha file from:', sha_url)
    try:
        shafile, header = request.urlretrieve(url=sha_url)
    except HTTPError as e:
        check_for_404_error(e)
        return False
    # Checksum for program package:
    sha = sha512_checksum(setupfile)
    if sha == Path(shafile).read_text():
        return True
    else:
        return False


def check_for_404_error(e):
    if e.code == 404:
        print('Could not download file!')


def sha512_checksum(filename, block_size=65536):
    """
    Calculates a SHA512 checksum from a file.
    """
    sha512 = hashlib.sha512()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha512.update(block)
    return sha512.hexdigest()


def kill_program_instances(program_name: str):
    subprocess.call(["taskkill", "/f", "/im", "{}.exe".format(program_name)], stdout=0, stderr=0)


def finalcif_is_still_running():
    return [x for x in os.popen('tasklist').readlines() if 'finalcif' in x.lower()]


def any_options_supplied():
    if len(sys.argv) > 3:
        return True
    else:
        return False


def run_updater(filename: str):
    subprocess.Popen([filename])


def remove_update_executable(filename: str) -> None:
    Path(filename).unlink()


if __name__ == '__main__':
    # print(sys.argv)
    fetch_update()
    sys.exit(0)
