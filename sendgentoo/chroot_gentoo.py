#!/usr/bin/env python3
# -*- coding: utf8 -*-

# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=W0511  # todo is encouraged
# pylint: disable=C0301  # line too long
# pylint: disable=R0902  # too many instance attributes
# pylint: disable=C0302  # too many lines in module
# pylint: disable=C0103  # single letter var names, func name too descriptive
# pylint: disable=R0911  # too many return statements
# pylint: disable=R0912  # too many branches
# pylint: disable=R0915  # too many statements
# pylint: disable=R0913  # too many arguments
# pylint: disable=R1702  # too many nested blocks
# pylint: disable=R0914  # too many local variables
# pylint: disable=R0903  # too few public methods
# pylint: disable=E1101  # no member for base
# pylint: disable=W0201  # attribute defined outside __init__
# pylint: disable=R0916  # Too many boolean expressions in if statement


import os
import sys
from pathlib import Path
from typing import ByteString
from typing import Generator
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence

import click
import sh
from enumerate_input import enumerate_input
#from kcl.userops import not_root
#from kcl.pathops import path_is_block_special
from kcl.fileops import write_line_to_file
#from getdents import files
from kcl.mountops import path_is_mounted
from retry_on_exception import retry_on_exception
#from collections import defaultdict
from run_command import run_command
#from with_sshfs import sshfs
from with_chdir import chdir


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint


# import pdb; pdb.set_trace()
# #set_trace(term_size=(80, 24))
# from pudb import set_trace; set_trace(paused=False)

##def log_uncaught_exceptions(ex_cls, ex, tb):
##   eprint(''.join(traceback.format_tb(tb)))
##   eprint('{0}: {1}'.format(ex_cls, ex))
##
##sys.excepthook = log_uncaught_exceptions


@click.command()
@click.argument("mount_path")
@click.option('--stdlib', required=False, type=click.Choice(['glibc', 'musl']), default="glibc")
@click.option('--boot-device', type=str, required=True)
@click.option('--hostname', type=str, required=True)
@click.option('--march', required=True, type=click.Choice(['native', 'nocona']))
@click.option('--root-filesystem', required=False, type=click.Choice(['ext4', 'zfs', '9p']), default="ext4")
@click.option('--newpasswd', type=str, required=True)
@click.option('--ip', type=str, required=True)
@click.option('--ip-gateway', type=str, required=True)
@click.option('--vm', required=False, type=click.Choice(['qemu']))
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option('--ipython', is_flag=True)
@click.pass_context
def cli(ctx,
        mount_path: str,
        stdlib: str,
        boot_device: str,
        hostname: str,
        march: str,
        root_filesystem: str,
        newpasswd: str,
        ip: str,
        ip_gateway: str,
        vm: str,
        sysskel,
        verbose: bool,
        debug: bool,
        ipython: bool,
        ):


    mount_path = Path(mount_path)

    command = "/home/cfg/_myapps/sendgentoo/sendgentoo/gpart_make_hybrid_mbr.sh {boot_device}".format(boot_device=boot_device)
    run_command(command, verbose=verbose, debug=debug, system=True)

    #if [[ "${vm}" == "qemu" ]];
    #then
    #    mount --bind "${destination}"{,-chroot} || { echo "${destination} ${destination}-chroot" ; exit 1 ; }
    #fi

    write_line_to_file(file_to_write=mount_path / Path('etc') / Path('conf.d') / Path('net'),
                       line='config_eth0="{ip}/24"'.format(ip=ip),
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    write_line_to_file(file_to_write=mount_path / Path('etc') / Path('conf.d') / Path('net'),
                       line='routes_eth0="default via {ip_gateway}"'.format(ip_gateway=ip_gateway),
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    write_line_to_file(file_to_write=mount_path / Path('etc') / Path('conf.d') / Path('hostname'),
                       line='hostname="{hostname}"'.format(hostname=hostname),
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    if not path_is_mounted(mount_path / Path('proc')):
        sh.mount('-t', 'proc', 'none', mount_path / Path('proc'))
    if not path_is_mounted(mount_path / Path('sys')):
        sh.mount('--rbind', '/sys', mount_path / Path('sys'))
    if not path_is_mounted(mount_path / Path('dev')):
        sh.mount('--rbind', '/dev', mount_path / Path('dev'))

    os.makedirs(mount_path / Path('usr') / Path('portage'), exist_ok=True)
    if not path_is_mounted(mount_path / Path('usr') / Path('portage')):
        sh.mount('--rbind', '/usr/portage', mount_path / Path('usr') / Path('portage'))

    os.makedirs(mount_path / Path('home') / Path('cfg'), exist_ok=True)

    os.makedirs(mount_path / Path('usr') / Path('local') / Path('portage'), exist_ok=True)

    with chdir('/home/'):
        rsync_command = ['rsync',
                         '--exclude="_priv"',
                         '--exclude="_myapps/gentoo"',
                         '--exclude="virt/iso"',
                         '--one-file-system',
                         '--delete',
                         '--perms',
                         '--executability',
                         '--human-readable',
                         '--verbose',
                         '--recursive',
                         '--links',
                         '--progress',
                         '--times',
                         '/home/cfg "${mount_path}/home/"'.format(mount_path=mount_path),]
        run_command(' '.join(rsync_command), system=True, ask=True, verbose=True)

    repos_conf = mount_path / Path('etc') / Path('portage') / Path('repos.conf')
    os.makedirs(repos_conf, exist_ok=True)
    sh.cp('/home/cfg/sysskel/etc/portage/repos.conf/gentoo.conf', repos_conf)

    gentoo_repo = mount_path / Path('var') / Path('db') / Path('repos') / Path('gentoo')
    os.makedirs(gentoo_repo, exist_ok=True)
    if not path_is_mounted(gentoo_repo):
        sh.mount('--rbind', '/var/db/repos/gentoo', gentoo_repo)

    sh.cp('/etc/portage/proxy.conf', mount_path / Path('etc') / Path('portage') / Path('proxy.conf'))

    write_line_to_file(file_to_write=mount_path / Path('etc') / Path('portage') / Path('make.conf'),
                       line='source /etc/portage/proxy.conf',
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    sh.cp('/usr/bin/ischroot', mount_path / Path('usr') / Path('bin') / Path('ischroot'))

    ic('Entering chroot')
    chroot_command = ['env',
                      '-i',
                      'HOME=/root',
                      'TERM=$TERM',
                      'chroot',
                      mount_path.as_posix(),
                      '/bin/bash',
                      '-l',
                      '-c',
                      'su',
                      '-',
                      '-c "/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot.sh {stdlib} {boot_device} {march} {root_filesystem} {newpasswd}"'.format(stdlib=stdlib, boot_device=boot_device, march=march, root_filesystem=root_filesystem, newpasswd=newpasswd),]
    run_command(' '.join(chroot_command), verbose=True, ask=True, system=True)

    ic('chroot_gentoo.py complete!')


if __name__ == '__main__':
    cli()
