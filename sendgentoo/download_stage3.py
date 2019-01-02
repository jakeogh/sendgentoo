#!/usr/bin/env python3

import requests
import click
from kcl.printops import eprint
from .get_stage3_url import get_stage3_url

def download_file(url, force=False):
    eprint("downloading:", url)
    local_filename = '/usr/portage/distfiles/' + url.split('/')[-1]
    #if force:
    #    os.unlink(local_filename)
    r = requests.get(url, stream=True)
    try:
        with open(local_filename, 'bx') as fh:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    fh.write(chunk)
    except FileExistsError:
        eprint("skipping download, file exists:", local_filename)
    r.close()
    return local_filename

def download_stage3(c_std_lib, multilib, url=False):
    if not url:
        url = get_stage3_url(c_std_lib=c_std_lib, multilib=multilib)
    eprint("url:", url)
    stage3_file = download_file(url)
    download_file(url + '.CONTENTS')
    download_file(url + '.DIGESTS')
    download_file(url + '.DIGESTS.asc')
    return stage3_file

@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']))
@click.option('--multilib', is_flag=True, required=False)
def main(c_std_lib, multilib):
    download_stage3(c_std_lib=c_std_lib, multilib=multilib)

if __name__ == '__main__':
    main()
