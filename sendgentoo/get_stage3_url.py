#!/usr/bin/env python3
import requests
import click
from kcl.printops import eprint

HELP="temp"

def download_file(url):
    local_filename = '/usr/portage/distfiles/' + url.split('/')[-1]
    r = requests.get(url, stream=True)
    try:
        with open(local_filename, 'bx') as fh:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    fh.write(chunk)
    except FileExistsError:
        eprint("skipping download, file exists:", local_filename)
    r.close()

def get_stage3_url(c_std_lib, multilib, arch):
    #mirror = 'http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/'
    mirror = 'http://gentoo.osuosl.org/releases/' + arch + '/autobuilds/'
    if c_std_lib == 'glibc':
        if not multilib:
            latest = 'latest-stage3-' + arch + '-hardened+nomultilib.txt'
        else:
            latest = 'latest-stage3-' + arch + '-hardened.txt'
    if c_std_lib == 'musl':
        latest = ''
        eprint("cant use musl yet")
        quit(1)
    if c_std_lib == 'uclibc':
        latest = 'latest-stage3-' + arch + '-uclibc-hardened.txt'
        eprint("uclibc wont compile efivars")
        quit(1)
    r = requests.get(mirror + latest)
    eprint(r)
    autobuild_file_lines = r.text.split('\n')
    r.close()
    for line in autobuild_file_lines:
        if 'stage3-' + arch in line:
            path = line.split(' ')[0]
            break
    #eprint('path:', path)
    assert 'stage3' in path
    url = mirror + path
    #eprint("url:", url)
    return url


@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']), help=HELP)
@click.option('--multilib', is_flag=True, required=False, help=HELP)
def main(c_std_lib, multilib):
    url = get_stage3_url(c_std_lib=c_std_lib, multilib=multilib)
    eprint(url)


if __name__ == '__main__':
    main()
