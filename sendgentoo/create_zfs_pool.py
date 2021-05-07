#!/usr/bin/env python3

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


import sys
from pathlib import Path

import click
from blocktool import get_block_device_size
from blocktool import path_is_block_special
from kcl.inputops import passphrase_prompt
from kcl.iterops import grouper
from mounttool import block_special_path_is_mounted
from run_command import run_command

from .setup_globals import RAID_LIST


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint


ASHIFT_HELP = '''9: 1<<9 == 512
10: 1<<10 == 1024
11: 1<<11 == 2048
12: 1<<12 == 4096
13: 1<<13 == 8192'''


@click.command()
@click.argument('devices', required=True, nargs=-1)
@click.option('--force', is_flag=True, required=False)
@click.option('--simulate', is_flag=True, required=False)
@click.option('--skip-checks', is_flag=True, required=False)
@click.option('--raid', is_flag=False, required=True, type=click.Choice(RAID_LIST))
@click.option('--raid-group-size', is_flag=False, required=True, type=int)
@click.option('--pool-name', is_flag=False, required=True, type=str)
@click.option('--ashift', is_flag=False, required=True, type=int, help=ASHIFT_HELP)
@click.option('--encrypt', is_flag=True)
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
#@click.option('--mount-point', is_flag=False, required=False, type=str)
#@click.option('--alt-root', is_flag=False, required=False, type=str)
def create_zfs_pool(devices,
                    force,
                    simulate,
                    skip_checks,
                    raid,
                    raid_group_size,
                    pool_name,
                    ashift,
                    verbose,
                    debug,
                    encrypt):
    if verbose:
        ic()
    assert ashift >= 9
    assert ashift <= 16
    eprint("using block size: {} (ashift={})".format(1<<ashift, ashift) )

    if skip_checks:
        assert simulate

    # https://raw.githubusercontent.com/ryao/zfs-overlay/master/zfs-install
    run_command("modprobe zfs || exit 1")

    for device in devices:
        if not skip_checks:
            assert path_is_block_special(device, follow_symlinks=True)
            assert not block_special_path_is_mounted(device, verbose=verbose, debug=debug,)
        if not (Path(device).name.startswith('nvme') or Path(device).name.startswith('mmcblk')):
            assert not device[-1].isdigit()

    if not skip_checks:
        first_device_size = get_block_device_size(devices[0])
        for device in devices:
            assert get_block_device_size(device) == first_device_size

    assert raid_group_size >= 1
    assert len(devices) >= raid_group_size

    device_string = ''
    if len(devices) == 1:
        assert raid == 'disk'
        device_string = devices[0]

    if len(devices) > 1:
        assert raid in ['mirror', 'raidz3']
        assert len(devices) % 2 == 0
        assert raid_group_size >= 2

    if len(devices) == 2:
        assert raid == 'mirror'
        device_string = "mirror " + devices[0] + ' ' + devices[1]

    if len(devices) > 2:
        if raid_group_size == 2:  # striped mirror raid10
            for pair in grouper(devices, 2):
                device_string = device_string + "mirror " + pair[0] + ' ' + pair[1] + ' '
                eprint("device_string:", device_string)
        elif raid_group_size == 4:
            for quad in grouper(devices, 4):
                assert False # a 4x mirror? or a 2x2 mirror?
                device_string = device_string + "mirror " + quad[0] + ' ' + quad[1] + ' ' + quad[2] + ' ' + quad[3] + ' '
                eprint("device_string:", device_string)
        elif raid_group_size in [8, 16]:
            assert raid == 'raidz3'
            device_string = "raidz3"
            for device in devices:
                device_string += " " + device
            eprint("device_string:", device_string)
        else:
            print("unknown mode")
            quit(1)

    assert device_string != ''
    assert len(pool_name) > 2

#    if alt_root:
#        alt_root = '-R ' + alt_root
#    else:
#        alt_root = ''
    #-o cachefile='/tmp/zpool.cache'\

    if encrypt:
        if not simulate:
            passphrase = passphrase_prompt("zpool", verbose=verbose, debug=debug,)
            passphrase = passphrase.decode('utf8')

    command = "zpool create"
    command += " -o feature@async_destroy=enabled"       # default   # Destroy filesystems asynchronously.
    command += " -o feature@empty_bpobj=enabled"         # default   # Snapshots use less space.
    command += " -o feature@lz4_compress=enabled"        # default   # (independent of the zfs compression flag)
    command += " -o feature@spacemap_histogram=enabled"  # default   # Spacemaps maintain space histograms.
    command += " -o feature@extensible_dataset=enabled"  # default   # Enhanced dataset functionality.
    command += " -o feature@bookmarks=enabled"           # default   # "zfs bookmark" command
    command += " -o feature@enabled_txg=enabled"         # default   # Record txg at which a feature is enabled
    command += " -o feature@embedded_data=enabled"       # default   # Blocks which compress very well use even less space.
    command += " -o feature@large_dnode=enabled"         # default   # Variable on-disk size of dnodes.
    command += " -o feature@large_blocks=enabled"        # default   # Support for blocks larger than 128KB.
    command += " -o ashift={}".format(ashift)            #           #
    command += " -o listsnapshots=on"

    if encrypt:
        command += " -o feature@encryption=enabled"
        command += " -O encryption=aes-256-gcm"
        command += " -O keyformat=passphrase"
        command += " -O keylocation=prompt"
        command += " -O pbkdf2iters=460000"

    command += " -O atime=off"                           #           # (dont write when reading)
    command += " -O compression=lz4"                     #           # (better than lzjb)
    command += " -O copies=1"                            #
    command += " -O xattr=off"                           #           # (sa is better than on)
    command += " -O sharesmb=off"                        #
    command += " -O sharenfs=off"                        #
    command += " -O checksum=fletcher4"                  # default
    command += " -O dedup=off"                           # default
    command += " -O utf8only=off"                        # default
    command += " -O mountpoint=none"                     # dont mount raw zpools
    command += " -O setuid=off"                          # only needed on rootfs
    command += ' ' + pool_name + ' ' + device_string

    ic(command)
    if not simulate:
        stdin = None
        if encrypt:
            stdin = passphrase
        run_command(command, verbose=True, expected_exit_status=0, stdin=stdin)

