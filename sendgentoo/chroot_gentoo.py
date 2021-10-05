#!/usr/bin/env python3
# -*- coding: utf8 -*-

# flake8: noqa
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
from asserttool import eprint
from asserttool import ic
from asserttool import root_user
from mounttool import mount_something
from mounttool import path_is_mounted
from pathtool import path_is_block_special
from pathtool import write_line_to_file
from run_command import run_command
from with_chdir import chdir

from .click_mesa_options import add_options
from .click_mesa_options import click_mesa_options


@click.command()
@click.argument("boot_device")
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
def make_hybrid_mbr(*,
                    boot_device: str,
                    verbose: bool,
                    debug: bool,
                    ):

    if not root_user():
        ic('You must be root.')
        sys.exit(1)

    assert path_is_block_special(boot_device)

    command = "/home/cfg/_myapps/sendgentoo/sendgentoo/gpart_make_hybrid_mbr.sh {boot_device}".format(boot_device=boot_device)
    run_command(command, verbose=verbose, debug=debug, system=True)


@click.command()
@click.argument("mount_path")
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
def rsync_cfg(*,
              mount_path: str,
              verbose: bool,
              debug: bool,
              ):

    if not root_user():
        ic('You must be root.')
        sys.exit(1)

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
                         '/home/cfg "{mount_path}/home/"'.format(mount_path=mount_path),]
        run_command(' '.join(rsync_command),
                    system=True,
                    ask=False,
                    verbose=True,)


@click.command()
@click.argument("mount_path")
@click.option('--stdlib', required=False, type=click.Choice(['glibc', 'musl']), default="glibc")
@click.option('--boot-device', type=str, required=True)
@click.option('--hostname', type=str, required=True)
@click.option('--march', required=True, type=click.Choice(['native', 'nocona']))
@click.option('--arch', is_flag=False, required=False, type=click.Choice(['alpha', 'amd64', 'arm', 'arm64', 'hppa', 'ia64', 'mips', 'ppc', 's390', 'sh', 'sparc', 'x86']), default="amd64")
@click.option('--root-filesystem', required=False, type=click.Choice(['ext4', 'zfs', '9p']), default="ext4")
@click.option('--newpasswd', type=str, required=True)
@click.option('--skip-to-rsync', is_flag=True)
@click.option('--ip', type=str, required=True)
@click.option('--ip-gateway', type=str, required=True)
@click.option('--pinebook-overlay', type=str, required=False)
@click.option('--vm', required=False, type=click.Choice(['qemu']))
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option('--ipython', is_flag=True)
@click.option('--kernel', is_flag=False, required=True, type=click.Choice(['gentoo-sources', 'pinebookpro-manjaro-sources']),default='gentoo-sources')
@add_options(click_mesa_options)
@click.pass_context
def chroot_gentoo(ctx,
                  mount_path: str,
                  stdlib: str,
                  boot_device: str,
                  hostname: str,
                  march: str,
                  arch: str,
                  root_filesystem: str,
                  newpasswd: str,
                  ip: str,
                  ip_gateway: str,
                  vm: str,
                  skip_to_rsync: bool,
                  mesa_use_enable: list[str],
                  mesa_use_disable: list[str],
                  pinebook_overlay: bool,
                  kernel: str,
                  verbose: bool,
                  debug: bool,
                  ipython: bool,
                  ):

    mount_path = Path(mount_path)
    assert path_is_mounted(mount_path, verbose=verbose, debug=debug,)

    if not skip_to_rsync:

        ctx.invoke(make_hybrid_mbr,
                   boot_device=boot_device,
                   verbose=verbose,
                   debug=debug,)

        #if [[ "${vm}" == "qemu" ]];
        #then
        #    mount --bind "${destination}"{,-chroot} || { echo "${destination} ${destination}-chroot" ; exit 1 ; }
        #fi

        write_line_to_file(path=mount_path / Path('etc') / Path('conf.d') / Path('net'),
                           line='config_eth0="{ip}/24"\n'.format(ip=ip),
                           unique=True,
                           verbose=verbose,
                           debug=debug,)

        write_line_to_file(path=mount_path / Path('etc') / Path('conf.d') / Path('net'),
                           line='routes_eth0="default via {ip_gateway}"\n'.format(ip_gateway=ip_gateway),
                           unique=True,
                           verbose=verbose,
                           debug=debug,)

        write_line_to_file(path=mount_path / Path('etc') / Path('conf.d') / Path('hostname'),
                           line='hostname="{hostname}"\n'.format(hostname=hostname),
                           unique=True,
                           verbose=verbose,
                           debug=debug,)

    mount_something(mountpoint=mount_path / Path('proc'), mount_type='proc', source=None, verbose=verbose, debug=debug)
    mount_something(mountpoint=mount_path / Path('sys'), mount_type='rbind', source=Path('/sys'), verbose=verbose, debug=debug)
    mount_something(mountpoint=mount_path / Path('dev'), mount_type='rbind', source=Path('/dev'), verbose=verbose, debug=debug)

    os.makedirs(mount_path / Path('home') / Path('cfg'), exist_ok=True)

    os.makedirs(mount_path / Path('usr') / Path('local') / Path('portage'), exist_ok=True)

    _var_tmp_portage = mount_path / Path('var') / Path('tmp') / Path('portage')
    os.makedirs(_var_tmp_portage, exist_ok=True)
    sh.chown('portage:portage', _var_tmp_portage)
    mount_something(mountpoint=_var_tmp_portage, mount_type='rbind', source=Path('/var/tmp/portage'), verbose=verbose, debug=debug)
    del _var_tmp_portage

    ctx.invoke(rsync_cfg,
               mount_path=mount_path,
               verbose=verbose,
               debug=debug,)

    _repos_conf = mount_path / Path('etc') / Path('portage') / Path('repos.conf')
    os.makedirs(_repos_conf, exist_ok=True)
    sh.cp('/home/cfg/sysskel/etc/portage/repos.conf/gentoo.conf', _repos_conf)
    del _repos_conf

    _gentoo_repo = mount_path / Path('var') / Path('db') / Path('repos') / Path('gentoo')
    os.makedirs(_gentoo_repo, exist_ok=True)
    mount_something(mountpoint=_gentoo_repo, mount_type='rbind', source=Path('/var/db/repos/gentoo'), verbose=verbose, debug=debug)
    del _gentoo_repo

    sh.cp('/etc/portage/proxy.conf', mount_path / Path('etc') / Path('portage') / Path('proxy.conf'))

    write_line_to_file(path=mount_path / Path('etc') / Path('portage') / Path('make.conf'),
                       line='source /etc/portage/proxy.conf\n',
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    write_line_to_file(path=mount_path / Path('etc') / Path('hosts'),
                       line='127.0.0.1\tlocalhost\t{hostname}\n'.format(hostname=hostname),
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    mesa_use = []
    for flag in mesa_use_enable:
        mesa_use.append(flag)
    for flag in mesa_use_disable:
        mesa_use.append('-' + flag)
    mesa_use = ' '.join(mesa_use)
    mesa_use = 'media-libs/mesa' + ' ' + mesa_use

    write_line_to_file(path=mount_path / Path('etc') / Path('portage') / Path('package.use') / Path('mesa'),
                       line=mesa_use + '\n',
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    sh.cp('/usr/bin/ischroot', mount_path / Path('usr') / Path('bin') / Path('ischroot'))  # bug for cross compile

    ic('Entering chroot')
    #chroot_command = ['env',
    #                  '-i',
    #                  'HOME=/root',
    #                  'TERM=$TERM',
    #                  'chroot',
    #                  Path(mount_path).as_posix(),
    #                  '/bin/bash',
    #                  '-l',
    #                  '-c',
    #                  'su',
    #                  '-',
    #                  '-c "/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot.sh {stdlib} {boot_device} {march} {root_filesystem} {newpasswd} {pinebook_overlay} {kernel}"'.format(stdlib=stdlib,
    #                                                                                                                                                                                boot_device=boot_device,
    #                                                                                                                                                                                march=march,
    #                                                                                                                                                                                root_filesystem=root_filesystem,
    #                                                                                                                                                                                newpasswd=newpasswd,
    #                                                                                                                                                                                pinebook_overlay=str(int(pinebook_overlay)),
    #                                                                                                                                                                                kernel=kernel)]

    chroot_binary = 'chroot'
    if arch != 'amd64':
        chroot_binary = 'fchroot'

    chroot_command = \
        ['env',
         '-i',
         'HOME=/root',
         'TERM=$TERM',
         chroot_binary,
         Path(mount_path).as_posix(),
         '/bin/bash',
         '-l',
         '-c',
         'su',
         '-',
         ]
    c_cmd = '-c "/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot.py --stdlib {stdlib} --boot-device {boot_device} --march {march} --root-filesystem {root_filesystem} --newpasswd {newpasswd} {pinebook_overlay} --kernel {kernel}"'
    c_cmd = c_cmd.format(stdlib=stdlib,
                         boot_device=boot_device,
                         march=march,
                         root_filesystem=root_filesystem,
                         newpasswd=newpasswd,
                         pinebook_overlay=('--pinebook-overlay' if pinebook_overlay else ''),
                         kernel=kernel)
    chroot_command.append(c_cmd)
    run_command(' '.join(chroot_command), verbose=True, ask=True, system=True)
    ic('chroot_gentoo.py complete!')
