#!/usr/bin/env python3

import click
import os
#import gnupg
from subprocess import CalledProcessError
from kcl.mountops import path_is_mounted
from kcl.fileops import file_exists
from kcl.command import run_command
from kcl.printops import ceprint
from kcl.printops import eprint
from .get_stage3_url import get_stage3_url
from .download_stage3 import download_stage3


def install_stage3(c_std_lib, multilib, arch, destination, vm, vm_ram):
    eprint("c_std_lib:", c_std_lib, "multilib:", multilib, "arch:", arch, "destination:", destination, "vm:", vm)
    os.chdir(destination)
    eprint("destination:", destination)
    eprint("os.getcwd():", os.getcwd())
    assert os.getcwd() == str(destination)
    if not vm:
        assert path_is_mounted(destination)
    url = get_stage3_url(c_std_lib=c_std_lib, multilib=multilib, arch=arch)
    stage3_file = download_stage3(c_std_lib=c_std_lib, multilib=multilib, url=url)
    assert file_exists(stage3_file)
    #gpg = gnupg.GPG(verbose=True)
    #import_result = gpg.recv_keys('keyserver.ubuntu.com', '0x2D182910')
    #ceprint(import_result)
    run_command('gpg --keyserver keyserver.ubuntu.com --recv-key 0x2D182910', verbose=True)
    ceprint("stage3_file:", stage3_file)
    run_command('gpg --verify ' + stage3_file + '.DIGESTS.asc', verbose=True)
    whirlpool = run_command("openssl dgst -r -whirlpool " + stage3_file + "| cut -d ' ' -f 1", verbose=True).decode('utf8').strip()
    try:
        run_command("/bin/grep " + whirlpool + ' ' + stage3_file + '.DIGESTS', verbose=True)
    except CalledProcessError:
        ceprint("BAD WHIRPOOL HASH:", whirlpool)
        ceprint("For file:", stage3_file)
        ceprint("File is corrupt (most likely partially downloaded). Delete it and try again.")
        quit(1)
    command = 'tar --xz -xpf ' + stage3_file + ' -C /mnt/gentoo'
    run_command(command, verbose=True)


#@click.command()
#@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']))
#@click.option('--multilib', is_flag=True, required=False)
#@click.option('--arch', is_flag=False, required=True, type=click.Choice(['alpha', 'amd64', 'arm', 'hppa', 'ia64', 'mips', 'ppc', 's390', 'sh', 'sparc', 'x86']))
#def main(c_std_lib, multilib, arch):
#    install_stage3(c_std_lib=c_std_lib, multilib=multilib, arch=arch)
#
#if __name__ == '__main__':
#    main()
