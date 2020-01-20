#!/usr/bin/env python3

import click
from kcl.printops import eprint
from kcl.netops import download_file
from kcl.netops import construct_proxy_dict

HELP="temp"


def get_stage3_url(c_std_lib, multilib, arch, proxy_dict):
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
    get_url = mirror + latest
    text = download_file(url=get_url, proxy_dict=proxy_dict)
    #r = requests.get(mirror + latest)
    eprint(text)
    autobuild_file_lines = text.split('\n')
    #r.close()
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
@click.option('--arch', is_flag=False, required=True, help=HELP, type=click.Choice(['amd64']))
@click.option('--proxy', is_flag=True)
def main(c_std_lib, multilib, arch, proxy):
    if proxy:
        proxy_dict = construct_proxy_dict()
    url = get_stage3_url(c_std_lib=c_std_lib, multilib=multilib, arch=arch, proxy_dict=proxy_dict)
    eprint(url)


if __name__ == '__main__':
    main()
