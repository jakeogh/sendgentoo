#!/usr/bin/env python3

import os
import sys
from subprocess import CalledProcessError

from kcl.netops import construct_proxy_dict
from mounttool import path_is_mounted
from pathtool import path_is_file
from run_command import run_command

from .download_stage3 import download_stage3
from .get_stage3_url import get_stage3_url


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint


def install_stage3(stdlib,
                   multilib: bool,
                   arch: str,
                   destination: str,
                   vm: bool,
                   vm_ram: int,
                   verbose: bool,
                   debug: bool,
                   ):
    ic(stdlib, multilib, arch, destination, vm)
    os.chdir(destination)
    ic(destination)
    ic(os.getcwd())
    assert os.getcwd() == str(destination)
    if not vm:
        assert path_is_mounted(destination, verbose=verbose, debug=debug,)
    proxy_dict = construct_proxy_dict()
    #ic(proxy)
    #assert proxy
    url = get_stage3_url(stdlib=stdlib, multilib=multilib, arch=arch, proxy_dict=proxy_dict)
    stage3_file = download_stage3(stdlib=stdlib, multilib=multilib, url=url, arch=arch, proxy_dict=proxy_dict)
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
    run_command('gpg --verify ' + stage3_file + '.DIGESTS.asc', verbose=True)
    whirlpool = run_command("openssl dgst -r -whirlpool " + stage3_file + "| cut -d ' ' -f 1", verbose=True).decode('utf8').strip()
    try:
        run_command("/bin/grep " + whirlpool + ' ' + stage3_file + '.DIGESTS', verbose=True)
    except CalledProcessError:
        ic('BAD WHIRPOOL HASH:', whirlpool)
        ic('For file:', stage3_file)
        ic('File is corrupt (most likely partially downloaded). Delete it and try again.')
        quit(1)
    command = 'tar --xz -xpf ' + stage3_file + ' -C ' + str(destination)
    run_command(command, verbose=True)

