#!/usr/bin/env python3

import time
import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.printops import eprint
from kcl.command import run_command
from .warn import warn

def write_grub_bios_partition(device, force, start, end, partition_number):
    eprint("creating grub_bios partition on device:", device, "partition_number:", partition_number, "start:", start, "end:", end)
    assert not device[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)

    if not force:
        warn((device,))

    #run_command("parted " + device + " --align optimal --script -- mkpart primary " + start + ' ' + end)
    run_command("parted " + device + " --align minimal --script -- mkpart primary " + start + ' ' + end)
    run_command("parted " + device + " --script -- name " + partition_number + " BIOSGRUB")
    run_command("parted " + device + " --script -- set " + partition_number + " bios_grub on")

#    parted size prefixes
#    "s" (sectors)
#    "B" (bytes)
#    "kB"
#    "MB"
#    "MiB"
#    "GB"
#    "GiB"
#    "TB"
#    "TiB"
#    "%" (percentage of device size)
#    "cyl" (cylinders)

    # sgdisk -a1 -n2:48:2047 -t2:EF02 -c2:"BIOS boot partition " + device # numbers in 512B sectors


@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--start',  is_flag=False, required=True, type=str)
@click.option('--end',    is_flag=False, required=True, type=str)
@click.option('--partition_number',    is_flag=False, required=True, type=str)
@click.option('--force',  is_flag=True,  required=False)
def main(device, start, end, force, partition_number):
    write_grub_bios_partition(device=device, start=start, end=end, force=force, partition_number=partition_number)


if __name__ == '__main__':
    main()
