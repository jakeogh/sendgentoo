#!/usr/bin/env python3

import os
import sys
import time
import click
import subprocess
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.command import run_command
from write_gpt import write_gpt

def write_grub_bios_partition(device, force, start='1MiB', end='3MiB'):

    print("creating grub_bios partition on:", device)
    assert not device[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)

    if not force:
        print("THIS WILL DESTROY ALL DATA ON:", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        print("Sleeping 5 seconds")
        time.sleep(5)

    run_command("parted " + device + " --script -- mkpart primary " + start + ' ' + end)
    run_command("parted " + device + " --script -- name 1 BIOS")
    run_command("parted " + device + " --script -- set 1 bios_grub on")


@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--start',  is_flag=False, required=False, type=str, default='1MiB')
@click.option('--end',    is_flag=False, required=False, type=str, default='3MiB')
@click.option('--force',  is_flag=True,  required=False)
def main(device, start, end, force):
    write_grub_bios_partition(device=device, start=start, end=end, force=force)

if __name__ == '__main__':
    main()
    quit(0)

