#!/usr/bin/env python3

import os
import click
import time
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.printops import eprint
from kcl.command import run_command
from destroy_block_device_head_and_tail import destroy_block_device_head_and_tail

def write_mbr(device, no_wipe, force, no_backup):
    eprint("writing MBR to:", device)
    assert not device[-1].isdigit()
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    if not force:
        eprint("THIS WILL DESTROY ALL DATA ON:", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        eprint("Sleeping 5 seconds")
        time.sleep(5)
    if not no_wipe:
        destroy_block_device_head_and_tail(device=device, force=force, no_backup=no_backup)
        #run_command("sgdisk --zap-all " + boot_device)

    run_command("parted " + device + " --script -- mklabel msdos")
    #run_command("parted " + device + " --script -- mklabel gpt")
    #run_command("sgdisk --clear " + device) #alt way to greate gpt label

@click.command()
@click.option('--device',     is_flag=False, required=True)
#@click.option('--device-partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
@click.option('--force',      is_flag=True,  required=False)
@click.option('--no-wipe',    is_flag=True,  required=False)
@click.option('--no-backup',  is_flag=True,  required=False)
def main(device, force, no_wipe, no_backup):
    write_mbr(device=device, force=force, no_wipe=no_wipe, no_backup=no_backup)

if __name__ == '__main__':
    main()
    quit(0)

