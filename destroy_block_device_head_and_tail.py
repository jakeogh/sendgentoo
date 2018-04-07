#!/usr/bin/env python3
import os
import click
import time
import subprocess
import sys
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.fileops import get_file_size
from backup_byte_range import backup_byte_range
from kcl.printops import eprint

def destroy_block_device_head(device, size, no_backup, note):
    #eprint("destroy_black_device_head()")
    #eprint("no_backup:", no_backup)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    zero_byte_range(device, 0, size, no_backup, note)

def destroy_block_device_tail(device, size, no_backup, note):
    #eprint("destroy_block_device_tail()")
    #eprint("no_backup:", no_backup)
    assert size > 0
    device_size = get_file_size(device)
    #eprint("device_size:", device_size)
    assert size <= device_size
    start = device_size - size
    #eprint("start:       ", start)
    assert start > 0
    #eprint("bytes to zero:", size)
    end = start + size
    zero_byte_range(device, start, end, no_backup, note)

def zero_byte_range(device, start, end, no_backup, note):
    #eprint("zero_byte_range()")
    #eprint("start:", start)
    #eprint("end:", end)
    #eprint("no_backup:", no_backup)
    assert start >= 0
    assert end > 0
    assert start < end
    if not no_backup:
        backup_byte_range(device, start, end, note)
    with open(device, 'wb') as dfh:
        bytes_to_zero = end - start
        assert bytes_to_zero > 0
        dfh.seek(start)
        dfh.write(bytearray(bytes_to_zero))

def destroy_block_device_head_and_tail(device, size=(512), note=False, force=False, no_backup=False):
    #run_command("sgdisk --zap-all " + device) #alt method
    #eprint("destroy_block_device_head_and_tail()")
    #eprint("no_backup:", no_backup)
    assert isinstance(no_backup, bool)
    assert not device[-1].isdigit()
    eprint("destroying device:", device)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    if not force:
        eprint("THIS WILL DESTROY ALL DATA ON ", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        eprint("Sleeping 5 seconds")
        time.sleep(5)

    destroy_block_device_head(device=device, size=size, note=note, no_backup=no_backup)
    destroy_block_device_tail(device=device, size=size, note=note, no_backup=no_backup)
    return

@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--size',   is_flag=False, required=False, type=int, default=(512))
@click.option('--note',   is_flag=False, required=False)
@click.option('--force',  is_flag=True,  required=False)
@click.option('--no-backup', is_flag=True,  required=False)
def main(device, size, note, force, no_backup):
    destroy_block_device_head_and_tail(device, size, note, force, no_backup)

if __name__ == '__main__':
    main()
    quit(0)


