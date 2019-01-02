#!/usr/bin/env python3

import click
import os
import gnupg
from kcl.mountops import path_is_mounted
from kcl.fileops import file_exists
from kcl.command import run_command
from kcl.printops import ceprint
from .get_stage3_url import get_stage3_url
from .download_stage3 import download_stage3


def install_stage3(c_std_lib, multilib):
    ceprint("c_std_lib:", c_std_lib, "multilib:", multilib)
    os.chdir('/mnt/gentoo')
    assert os.getcwd() == '/mnt/gentoo'
    assert path_is_mounted('/mnt/gentoo')
    url = get_stage3_url(c_std_lib=c_std_lib, multilib=multilib)
    stage3_file = download_stage3(c_std_lib=c_std_lib, multilib=multilib, url=url)
    assert file_exists(stage3_file)
    #gpg = gnupg.GPG(verbose=True)
    #import_result = gpg.recv_keys('keyserver.ubuntu.com', '0x2D182910')
    #ceprint(import_result)
    run_command('gpg --keyserver keyserver.ubuntu.com --recv-key 0x2D182910', verbose=True)
    ceprint("stage3_file:", stage3_file)
    run_command('gpg --verify ' + stage3_file + '.DIGESTS.asc')
    command = 'tar --xz -xpf ' + stage3_file + ' -C /mnt/gentoo'
    run_command(command, verbose=True)

@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']))
@click.option('--multilib', is_flag=True, required=False)
def main(c_std_lib, multilib):
    install_stage3(c_std_lib=c_std_lib, multilib=multilib)


if __name__ == '__main__':
    main()
