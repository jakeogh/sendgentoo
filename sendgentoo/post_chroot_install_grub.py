#!/usr/bin/env python3
# -*- coding: utf8 -*-

# flake8: noqa           # flake8 has no per file settings :(
# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=C0114  #      Missing module docstring (missing-module-docstring)
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
# pylint: disable=C0305  # Trailing newlines editor should fix automatically, pointless warning
# pylint: disable=C0413  # TEMP isort issue [wrong-import-position] Import "from pathlib import Path" should be placed at the top of the module [C0413]


import os
import sys
import time
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal

import click
import sh

signal(SIGPIPE, SIG_DFL)
from pathlib import Path
from typing import ByteString
from typing import Generator
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

#from with_sshfs import sshfs
#from with_chdir import chdir
from asserttool import eprint
from asserttool import ic
from asserttool import nevd
from asserttool import validate_slice
from asserttool import verify
from enumerate_input import enumerate_input
from mounttool import path_is_mounted
#from asserttool import not_root
#from pathtool import path_is_block_special
from pathtool import write_line_to_file
from portagetool import install_package
from retry_on_exception import retry_on_exception
from timetool import get_timestamp

#from getdents import files
#from prettytable import PrettyTable
#output_table = PrettyTable()



#@with_plugins(iter_entry_points('click_command_tree'))
#@click.group()
#@click.option('--verbose', is_flag=True)
#@click.option('--debug', is_flag=True)
#@click.pass_context
#def cli(ctx,
#        verbose: bool,
#        debug: bool,
#        ):
#
#    null, end, verbose, debug = nevd(ctx=ctx,
#                                     printn=False,
#                                     ipython=False,
#                                     verbose=verbose,
#                                     debug=debug,)


# update setup.py if changing function name
@click.command()
@click.argument("boot_device",
                type=click.Path(exists=True,
                                dir_okay=False,
                                file_okay=True,
                                allow_dash=False,
                                path_type=Path,),
                nargs=1,
                required=True,)
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.pass_context
def cli(ctx,
        boot_device: Path,
        verbose: bool,
        debug: bool,
        ):

    null, end, verbose, debug = nevd(ctx=ctx,
                                     printn=False,
                                     ipython=False,
                                     verbose=verbose,
                                     debug=debug,)

    if not path_is_mounted(Path("/boot/efi"), verbose=verbose, debug=debug,):
        ic("/boot/efi not mounted. Exiting.")
        sys.exit(1)

    sh.env_update()
    #set +u # disable nounset        # line 22 has an unbound variable: user_id /etc/profile.d/java-config-2.sh
    #source /etc/profile || exit 1
    #set -o nounset

    install_package('grub')

    #if [[ "${root_filesystem}" == "zfs" ]];
    #then
    #    echo "GRUB_PRELOAD_MODULES=\"part_gpt part_msdos zfs\"" >> /etc/default/grub
    #   #echo "GRUB_CMDLINE_LINUX_DEFAULT=\"boot=zfs root=ZFS=rpool/ROOT\"" >> /etc/default/grub
    #   #echo "GRUB_CMDLINE_LINUX_DEFAULT=\"boot=zfs\"" >> /etc/default/grub
    #   #echo "GRUB_DEVICE=\"ZFS=rpool/ROOT/gentoo\"" >> /etc/default/grub
    #   # echo "GRUB_DEVICE=\"ZFS=${hostname}/ROOT/gentoo\"" >> /etc/default/grub #this was uncommented, disabled to not use hostname
    #else
    write_line_to_file(path=Path('/etc/default/grub'),
                       line='GRUB_PRELOAD_MODULES="part_gpt part_msdos"' + '\n',
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    root_partition_command = sh.Command('/home/cfg/linux/disk/get_root_device')
    root_partition = root_partition_command()
    ic("-------------- root_partition: {root_partition} ---------------------".format(root_partition=root_partition))
    partition_uuid_command = sh.Command('/home/cfg/linux/hardware/disk/blkid/PARTUUID')
    partuuid = partition_uuid_command(root_partition)
    ic("GRUB_DEVICE partuuid: {partuuid}".format(partuuid=partuuid))

    write_line_to_file(path=Path('/etc/default/grub'),
                       line='GRUB_DEVICE="PARTUUID={partuuid}"'.format(partuuid=partuuid) + '\n',
                       unique=True,
                       verbose=verbose,
                       debug=debug,)
    partuuid_root_device_command = sh.Command('/home/cfg/linux/disk/blkid/PARTUUID_root_device')
    partuuid_root_device = partuuid_root_device_command()


    partuuid_root_device_fstab_line = 'PARTUUID=' + partuuid_root_device + '\t/' + '\text4' + '\tnoatime' + '\t0'+ '\t1'
    write_line_to_file(path=Path('/etc/fstab'),
                       line=partuuid_root_device_fstab_line + '\n',
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    #grep -E "^GRUB_CMDLINE_LINUX=\"net.ifnames=0 rootflags=noatime irqpoll\"" /etc/default/grub || { echo "GRUB_CMDLINE_LINUX=\"net.ifnames=0 rootflags=noatime irqpoll\"" >> /etc/default/grub ; }
    write_line_to_file(path=Path('/etc/default/grub'),
                       line='GRUB_CMDLINE_LINUX="net.ifnames=0 rootflags=noatime intel_iommu=off"' + '\n',
                       unique=True,
                       verbose=verbose,
                       debug=debug,)

    sh.ln('-sf', '/proc/self/mounts', '/etc/mtab')

    sh.grub_install('--compress=no', '--target=x86_64-efi', '--efi-directory=/boot/efi', '--boot-directory=/boot', '--removable', '--recheck', '--no-rs-codes', boot_device, _out=sys.stdout, _err=sys.stderr)
    sh.grub_install('--compress=no', '--target=i386-pc', '--boot-directory=/boot', '--recheck', '--no-rs-codes', boot_device, _out=sys.stdout, _err=sys.stderr)

    sh.grub_mkconfig('-o', '/boot/grub/grub.cfg', _out=sys.stdout, _err=sys.stderr)

    with open('/install_status', 'a') as fh:
        fh.write(get_timestamp() + sys.argv[0] + 'complete'  + '\n')


if __name__ == '__main__':
    # pylint: disable=E1120
    cli()








