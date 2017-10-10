#!/usr/bin/env python3

import requests
import click
#import sys
import os
from gentoo_setup_get_stage3_url import get_stage3_url
from gentoo_setup_download_stage3 import download_stage3
from kcl.mountops import path_is_mounted
from kcl.fileops import file_exists
from kcl.command import run_command
import gnupg
from kcl.printops import eprint

HELP="temp"

def install_stage3(c_std_lib, multilib):
    os.chdir('/mnt/gentoo')
    assert os.getcwd() == '/mnt/gentoo'
    assert path_is_mounted('/mnt/gentoo')
    url = get_stage3_url(c_std_lib=c_std_lib, multilib=multilib)
    stage3_file = download_stage3(c_std_lib=c_std_lib, multilib=multilib, url=url)
    assert file_exists(stage3_file)
    gpg = gnupg.GPG(verbose=True)
    #import_result = gpg.recv_keys('keyserver.ubuntu.com', '0x2D182910')
    #eprint(import_result)
    run_command('gpg --keyserver keyserver.ubuntu.com --recv-key 0x2D182910', verbose=True)
    eprint("stage3_file:", stage3_file)
    command = 'tar xjpf ' + stage3_file + ' -C /mnt/gentoo'
    run_command(command, verbose=True)

@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']), help=HELP)
@click.option('--multilib', is_flag=True, required=False, help=HELP)
def main(c_std_lib):
    install_stage3(c_std_lib=c_std_lib, multilib=multilib)

if __name__ == '__main__':
    main()


#cd /mnt/gentoo || exit 1
#stage_path=`curl -s http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/latest-stage3-amd64-hardened+nomultilib.txt | tail -n 1 | cut -d ' ' -f 1`
#stage_file=`curl -s http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/latest-stage3-amd64-hardened+nomultilib.txt | tail -n 1 | cut -d '/' -f 3 | cut -d ' ' -f 1`
#
#echo "stage_file: ${stage_file}"
#
#wget "http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/${stage_path}" || exit 1
#wget "http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/${stage_path}.CONTENTS" || exit 1
#wget "http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/${stage_path}.DIGESTS" || exit 1
#wget "http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/${stage_path}.DIGESTS.asc" || exit 1
#gpg --keyserver keyserver.ubuntu.com --recv-key 0x2D182910
#gpg --verify "${stage_file}.DIGESTS.asc"
#tar xjpf stage3-*.tar.bz2 || exit 1

