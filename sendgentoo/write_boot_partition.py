#!/usr/bin/env python3

import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.command import run_command
from kcl.printops import eprint
from kcl.deviceops import warn


@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--force', is_flag=True, required=False)
def write_boot_partition(device, force):
    eprint("creating boot partition  (for grub config, stage2, vmlinuz) on:", device)
    assert not device[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)

    if not force:
        warn((device,))

    partition_number = '3'
    start = "100MiB"
    end = "400MiB"

    run_command("parted -a optimal " + device + " --script -- mkpart primary " + start + ' ' + end)
    run_command("parted  " + device + " --script -- name " + partition_number + " bootfs")
    run_command("mkfs.ext4 " + device + partition_number)
