#!/usr/bin/env python3

import click
from kcl.printops import eprint
from kcl.netops import download_file
from .get_stage3_url import get_stage3_url


def download_stage3(c_std_lib, multilib, arch, proxy, url=False):
    if not url:
        url = get_stage3_url(c_std_lib=c_std_lib, multilib=multilib, arch=arch)
    eprint("url:", url)
    destination_dir = '/usr/portage/distfiles/'
    stage3_file = download_file(url, destination_dir, proxy=proxy)
    download_file(url + '.CONTENTS', destination_dir, proxy=proxy)
    download_file(url + '.DIGESTS', destination_dir, proxy=proxy)
    download_file(url + '.DIGESTS.asc', destination_dir, proxy=proxy)
    return stage3_file


@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']))
@click.option('--arch', is_flag=False, required=True, type=click.Choice(['alpha', 'amd64', 'arm', 'hppa', 'ia64', 'mips', 'ppc', 's390', 'sh', 'sparc', 'x86']))
@click.option('--multilib', is_flag=True, required=False)
@click.option('--proxy', is_flag=False, required=False)
def main(c_std_lib, arch, multilib, proxy):
    download_stage3(c_std_lib=c_std_lib, multilib=multilib, arch=arch, proxy=proxy)


if __name__ == '__main__':
    main()
