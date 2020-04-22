#!/usr/bin/env python3

#import click
import os
from icecream import ic
#import gnupg
from subprocess import CalledProcessError
from kcl.mountops import path_is_mounted
from kcl.fileops import path_is_file
#from kcl.fileops import read_file_bytes
from kcl.commandops import run_command
from kcl.printops import ceprint
from kcl.printops import eprint
from kcl.netops import construct_proxy_dict
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
    #proxy_config = read_file_bytes('/etc/portage/proxy.conf').decode('utf8').split('\n')
    #ic(proxy_config)
    ##proxy = None
    #proxy_dict = {}
    #for line in proxy_config:
    #    line = line.split('=')[-1]
    #    line = line.strip('"')
    #    scheme = line.split('://')[0]
    #    ic(scheme)
    #    proxy_dict[scheme] = line
    #    #proxy = line.split('://')[-1].split('"')[0]
    proxy_dict = construct_proxy_dict()
    #ic(proxy)
    #assert proxy
    url = get_stage3_url(c_std_lib=c_std_lib, multilib=multilib, arch=arch, proxy_dict=proxy_dict)
    stage3_file = download_stage3(c_std_lib=c_std_lib, multilib=multilib, url=url, arch=arch, proxy_dict=proxy_dict)
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
    command = 'tar --xz -xpf ' + stage3_file + ' -C ' + str(destination)
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
