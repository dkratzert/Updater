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
from contextlib import suppress
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

from progressbar import ProgressBar

"""
return codes:
0: regular end
2: HTTP error 404 (unable to download)
3: can not kill program instance prior to update
4: No command line options supplied
"""

download_urls = {
    # The URLs are a list in order to make different locations possible:
    'dsr'            : [
        'https://dkratzert.de/files/DSR/DSR-setup-{}.exe',
        'https://xs3-data.uni-freiburg.de/data/DSR-setup-{}.exe',
        'https://github.com/dkratzert/DSR/raw/master/DSR-setup-{}.exe',
    ],
    'structurefinder': [
        'https://dkratzert.de/files/structurefinder/StructureFinder-setup-x64-v{}.exe',
        'https://xs3-data.uni-freiburg.de/structurefinder/StructureFinder-setup-x64-v{}.exe',
        'https://github.com/dkratzert/Structurefinder/raw/master/StructureFinder-setup-x64-v{}.exe',
    ],
    'finalcif'       : [
        'https://dkratzert.de/files/finalcif/FinalCif-setup-x64-v{}.exe',
        'https://xs3-data.uni-freiburg.de/finalcif/FinalCif-setup-x64-v{}.exe',
        'https://github.com/dkratzert/FinalCif/raw/master/FinalCif-setup-x64-v{}.exe',
    ],
    'test'           : [
        'https://dkratzert.de/files/test-v{}.exe',
        'https://xs3-data.uni-freiburg.de/test/test-v{}.exe',
        'https://github.com/dkratzert/FinalCif/raw/master/test-v{}.exe',
    ],
}


def show_help() -> None:
    print('############ Program updater V5 #################')
    print('Command line options:')
    print('-v version  : Version number of the installer executable')
    print('-p name     : Program name')
    if platform_is("win"):
        os.system('pause')


def get_options_index(option: str):
    return sys.argv.index(option)


def get_option(option: str = '') -> str:
    if option in sys.argv and get_options_index(option):
        value = sys.argv[get_options_index(option) + 1]
        return value
    return ''


def show_progress(block_num, block_size, total_size) -> None:
    pbar = ProgressBar(maxval=total_size)
    pbar.start()
    downloaded = block_num * block_size
    if downloaded < total_size:
        pbar.update(downloaded)
    else:
        pbar.finish()


def fetch_update() -> None:
    if not any_options_supplied():
        show_help()
        sys.exit(4)
    version = get_option('-v')
    program_name = get_option('-p')
    urls = download_urls.get(program_name)
    if not urls:
        print('Unknown program. Aborting update!')
        return None
    # This is the program setup that installs the new version:
    program_path = Path('{}-setup.exe'.format(program_name))
    kill_program_instances(program_name)
    if programm_is_still_running(program_name):
        sys.exit(3)
    tmp_dir = Path(__file__).parent
    downloaded_update = perform_download(program_path, tmp_dir, urls, version)
    if downloaded_update:
        run_updater(downloaded_update)
        print('Finished successfully.')
    else:
        print('\nGiving up.')
        if platform_is("win"):
            os.system("pause")
    return None


def perform_download(program_path, tmp_dir, urls, version) -> str:
    for url in urls:
        full_url = url.format(version)
        print('Downloading setup file from:', full_url)
        file_name = try_download(program_path, tmp_dir, full_url)
        checksum_state = check_checksum(file_name, url, version)
        if checksum_state:
            return file_name
        else:
            print('Failed to update, trying different URL...\n')
    return ''


def check_checksum(file_name: str, url: str, version: str) -> bool:
    shafile = download_checksum(sha_url=url.format(version))
    if not shafile:
        print('No checksum file found at URL.')
        return False
    if is_checksum_valid(file_name, shafile=shafile):
        print('Checksum OK')
        return True
    else:
        print('Checksum Failed. Update with this file not possible.')
        return False


def platform_is(plat: str) -> bool:
    return sys.platform.startswith(plat)


def try_download(program_path: Path, tmp_dir: Path, full_url: str) -> str:
    try:
        file_name, header = request.urlretrieve(url=full_url,
                                                filename=tmp_dir.joinpath(program_path),
                                                reporthook=show_progress)
    except (HTTPError, ValueError):
        print('Download failed.')
        return ''
    if file_name:
        print('-> Download succeeded.')
        return file_name


def is_checksum_valid(setupfile: str, shafile: str) -> bool:
    # download SHA file:
    if shafile:
        # Checksum for program package:
        sha_from_setup_file = sha512_checksum(setupfile)
        sha_from_sha_file = Path(shafile).read_text()
        return checksums_match(sha_from_setup_file, sha_from_sha_file)
    else:
        return False


def download_checksum(sha_url):
    shafile = ''
    sha_url = str(sha_url)[:-4] + '-sha512.sha'
    with suppress(HTTPError, ValueError):
        shafile, header = request.urlretrieve(url=sha_url, reporthook=show_progress)
    return shafile


def checksums_match(sha_of_setup: str, sha_of_sha_file: str) -> bool:
    if sha_of_setup == sha_of_sha_file:
        return True
    else:
        return False


def sha512_checksum(filename, block_size=65536) -> str:
    """
    Calculates a SHA512 checksum from a file.
    """
    sha512 = hashlib.sha512()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha512.update(block)
    return sha512.hexdigest()


def kill_program_instances(program_name: str) -> None:
    if platform_is("linux"):
        print()
    elif platform_is("darwin"):
        print()
    elif platform_is("win"):
        subprocess.call(["taskkill", "/f", "/im", "{}.exe".format(program_name)], stdout=0, stderr=0, shell=True)
        subprocess.call(["cls"], shell=True)


def programm_is_still_running(program: str) -> bool:
    if platform_is("linux"):
        return False
    elif platform_is("darwin"):
        return False
    elif platform_is("win"):
        return any([x for x in os.popen('tasklist').readlines() if program in x.lower()])


def any_options_supplied() -> bool:
    if len(sys.argv) > 3:
        return True
    else:
        return False


def run_updater(filename: str) -> bool:
    if platform_is("linux"):
        print('No update possible in Linux.')
        return False
    elif platform_is("darwin"):
        print('No update possible in MacOS.')
        return False
    elif platform_is("win"):
        subprocess.Popen([filename])
        return True


if __name__ == '__main__':
    # print(sys.argv)
    fetch_update()
    sys.exit(0)
