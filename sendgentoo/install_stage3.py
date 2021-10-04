#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from subprocess import CalledProcessError

import sh
from asserttool import eprint
from asserttool import ic
from mounttool import path_is_mounted
from nettool import construct_proxy_dict
from pathtool import path_is_file
from run_command import run_command
from with_chdir import chdir

from .download_stage3 import download_stage3


def install_stage3(stdlib,
                   multilib: bool,
                   arch: str,
                   destination: Path,
                   distfiles_dir: Path,
                   vm: str,
                   vm_ram: int,
                   verbose: bool,
                   debug: bool,
                   ):

    destination = Path(destination)
    distfiles_dir = Path(distfiles_dir)
    ic(stdlib, multilib, arch, destination, vm)
    #os.chdir(destination)
    ic(destination)
    if not vm:
        assert path_is_mounted(destination, verbose=verbose, debug=debug,)
    with chdir(destination):
        ic(os.getcwd())
        assert os.getcwd() == str(destination)
        proxy_dict = construct_proxy_dict(verbose=verbose, debug=debug,)
        #url = get_stage3_url(stdlib=stdlib, multilib=multilib, arch=arch, proxy_dict=proxy_dict)
        #stage3_file = download_stage3(stdlib=stdlib, multilib=multilib, url=url, arch=arch, proxy_dict=proxy_dict)
        stage3_file = download_stage3(destination_dir=distfiles_dir, stdlib=stdlib, multilib=multilib, arch=arch, proxy_dict=proxy_dict)
        assert path_is_file(stage3_file)

        # this never worked
        #gpg = gnupg.GPG(verbose=True)
        #import_result = gpg.recv_keys('keyserver.ubuntu.com', '0x2D182910')
        #ceprint(import_result)

        ## this works sometimes, but now complaines abut no dirmngr
        #gpg_cmd = 'gpg --keyserver keyserver.ubuntu.com --recv-key 0x2D182910'
        ##if proxy:
        ##    keyserver_options = " --keyserver-options http_proxy=http://" + proxy
        ##    gpg_cmd += keyserver_options
        #run_command(gpg_cmd, verbose=True)

        ic(stage3_file)
        for line in sh.gpg('--verify', '--verbose', stage3_file.as_posix() + '.DIGESTS.asc', _iter=True):
            eprint(line, end='')

        #whirlpool = run_command("openssl dgst -r -whirlpool " + stage3_file.as_posix() + "| cut -d ' ' -f 1",
        #                        verbose=True).decode('utf8').strip()
        #try:
        #    run_command("/bin/grep " + whirlpool + ' ' + stage3_file.as_posix() + '.DIGESTS', verbose=True)
        #except CalledProcessError:
        #    ic('BAD WHIRPOOL HASH:', whirlpool)
        #    ic('For file:', stage3_file)
        #    ic('File is corrupt (most likely partially downloaded). Delete it and try again.')
        #    sys.exit(1)
        command = 'tar --xz -xpf ' + stage3_file.as_posix() + ' -C ' + destination.as_posix()
        run_command(command, verbose=True)

