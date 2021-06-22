#!/usr/bin/env python3

import click
from kcl.printops import eprint
from kcl.netops import download_file
from kcl.netops import construct_proxy_dict
from .get_stage3_url import get_stage3_url


def download_stage3(stdlib, multilib, arch, proxy_dict, url=False):
    if not url:
        url = get_stage3_url(stdlib=stdlib, multilib=multilib, arch=arch)
    eprint("url:", url)
    destination_dir = '/usr/portage/distfiles/'
    stage3_file = download_file(url, destination_dir, proxy_dict=proxy_dict)
    download_file(url + '.CONTENTS', destination_dir, proxy_dict=proxy_dict)
    download_file(url + '.DIGESTS', destination_dir, proxy_dict=proxy_dict)
    download_file(url + '.DIGESTS.asc', destination_dir, proxy_dict=proxy_dict)
    return stage3_file


@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']))
@click.option('--arch', is_flag=False, required=True, type=click.Choice(['alpha', 'amd64', 'arm', 'hppa', 'ia64', 'mips', 'ppc', 's390', 'sh', 'sparc', 'x86']))
@click.option('--multilib', is_flag=True, required=False)
@click.option('--proxy', is_flag=True)
def main(stdlib, arch, multilib, proxy):
    if proxy:
        proxy_dict = construct_proxy_dict()
    download_stage3(stdlib=stdlib, multilib=multilib, arch=arch, proxy_dict=proxy_dict)


if __name__ == '__main__':
    main()
