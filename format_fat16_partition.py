#!/usr/bin/env python3

import time
import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.command import run_command
from kcl.printops import ceprint

def format_fat16_partition(device, force):
    ceprint("formatting fat16 partition on:", device)
    assert device[-1].isdigit()
    assert path_is_block_special(device)  # oddly, this failed on '/dev/sda2', maybe the kernel was not done digesting the previous table change?
    assert not block_special_path_is_mounted(device)

    if not force:
        ceprint("THIS WILL DESTROY ALL DATA ON:", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        ceprint("Sleeping 5 seconds")
        time.sleep(5)

    run_command("mkfs.fat -F16 -s2 " + device)

    # 127488 /mnt/sdb2/EFI/BOOT/BOOTX64.EFI


@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--force',  is_flag=True,  required=False)
def main(device, force):
    format_fat16_partition(device=device, force=force)


if __name__ == '__main__':
    main()
