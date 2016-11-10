#!/usr/bin/env python3
import os
import click
import time
import subprocess
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.fileops import get_file_size

def destroy_block_device_head(device, size, backup, note):
    print("destroy_black_device_head()")
    print("backup:", backup)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    zero_byte_range(device, 0, size, backup, note)
    #return True

def destroy_block_device_tail(device, size, backup, note):
    print("destroy_block_device_tail()")
    print("backup:", backup)
    assert size > 0
    device_size = get_file_size(device)
    #print("device_size:", device_size)
    assert size <= device_size
    start = device_size - size
    #print("start:       ", start)
    assert start > 0
    #print("bytes to zero:", size)
    end = start + size
    zero_byte_range(device, start, end, backup, note)
    #return True

def zero_byte_range(device, start, end, backup, note):
    #print("zero_byte_range()")
    #print("start:", start)
    #print("end:", end)
    print("backup:", backup)
    assert start >= 0
    assert end > 0
    assert start < end
    if backup:
        backup_byte_range(device, start, end, note)
    with open(device, 'wb') as dfh:
        bytes_to_zero = end - start
        assert bytes_to_zero > 0
        dfh.seek(start)
        dfh.write(bytearray(bytes_to_zero))

def backup_byte_range(device, start, end, note):
    print("backup_byte_range()")
    with open(device, 'rb') as dfh:
        bytes_to_read = end - start
        assert bytes_to_read > 0
        dfh.seek(start)
        bytes_read = dfh.read(bytes_to_read)
        assert len(bytes_read) == bytes_to_read

    timestamp = str(time.time())
    device_string = device.replace('/', '_')
    backup_file_tail = '_.' + device_string + '.' + timestamp + '_start_' + str(start) + '_end_' + str(end) + '.bak'
    if note:
        backup_file = '_backup_' + note + backup_file_tail
    else:
        backup_file = '_backup__.' + backup_file_tail
    with open(backup_file, 'xb') as bfh:
        bfh.write(bytes_read)

def destroy_block_device_head_and_tail(device, size=(1024*1024*128), note=False, force=False, backup=False):
    print("destroy_block_device_head_and_tail()")
    print("backup:", backup)
    assert isinstance(backup, bool)
    assert not device[-1].isdigit()
    print("destroying device:", device)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    if not force:
        print("THIS WILL DESTROY ALL DATA ON ", device, "_REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO ACCIDENTLY DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        print("Sleeping 5 seconds")
        time.sleep(5)

    destroy_block_device_head(device=device, size=size, note=note, backup=backup)
    destroy_block_device_tail(device=device, size=size, note=note, backup=backup)
    return

@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--size',   is_flag=False, required=False, type=int, default=(1024*1024*128))
@click.option('--note',   is_flag=False, required=False)
@click.option('--force',  is_flag=True,  required=False)
@click.option('--backup', is_flag=True,  required=False, default=False)
def main(device, size, note, force, backup):
    print("backup:", backup)
    destroy_block_device_head_and_tail(device, size, note, force, backup)

if __name__ == '__main__':
    main()
    quit(0)


