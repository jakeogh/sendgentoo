#!/usr/bin/env python3

import os
import sys
import click
import time
import subprocess
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.command import run_command
#from destroy_block_device_head_and_tail import destroy_block_device_head_and_tail
from write_gpt import write_gpt
from write_grub_bios_partition import write_grub_bios_partition
from write_efi_partition import write_efi_partition
from kcl.printops import eprint
from format_fat16_partition import format_fat16_partition

def create_boot_device(device, partition_table, filesystem, force):
    assert not device[-1].isdigit()
    eprint("installing gpt/grub/efi on boot device:", device, '(' + partition_table + ')', '(' + filesystem + ')')
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    assert os.getcwd() == '/home/cfg/setup/gentoo_installer'

    if not force:
        eprint("THIS WILL DESTROY ALL DATA ON", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        eprint("Sleeping 5 seconds")
        time.sleep(5)

    # dont do this here, want to be able to let zfs make the gpt and it's partitions before making bios_grub and EFI
    #destroy_block_device_head_and_tail(device=device, force=True)

    if partition_table == 'gpt':
        if filesystem != 'zfs':
            write_gpt(device, no_wipe=True, force=force, no_backup=False) # zfs does this

    if filesystem == 'zfs':
        write_grub_bios_partition(device=device, force=True, start='48s', end='1023s', partition_number='2') #2 if zfs made sda1 and sda9
    else:
        write_grub_bios_partition(device=device, force=True, start='48s', end='1023s', partition_number='1')

    if filesystem != 'zfs':
        write_efi_partition(device=device, force=True, start='1024s', end='18047s', partition_number='2') # this is /dev/sda9 on zfs

    if filesystem == 'zfs':
        format_fat16_partition(device=device+'9', force=True)

@click.command()
@click.option('--device',          is_flag=False, required=True)
@click.option('--partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
@click.option('--filesystem',      is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
@click.option('--force',           is_flag=True,  required=False)
def main(device, partition_table, filesystem, force):
    create_boot_device(device=device, partition_table=partition_table, filesystem=filesystem, force=force)

if __name__ == '__main__':
    main()
    quit(0)

#boot_partition_command = "parted -a optimal " + boot_device + " --script -- mkpart primary 200MiB 331MiB"
#run_command(boot_partition_command)
#set_boot_name_command = "parted -a optimal " + boot_device + " --script -- name 2 grub"
#run_command(set_boot_name_command)
#command = "mkfs.ext4 " + boot_device + "2"
#run_command(command)

#set_boot_on_command = "parted -a optimal " + boot_device + " --script -- set 2 boot on"
#run_command(set_boot_on_command)
#root_partition_boot_flag_command = "parted -a optimal " + boot_device + " --script -- set 2 boot on"
#run_command(root_partition_boot_flag_command)
