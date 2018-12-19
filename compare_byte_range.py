#!/usr/bin/env python3

#import sys
import click
#import time
#from kcl.time import timestamp
import os
from backup_byte_range import backup_byte_range
from kcl.printops import eprint

def compare_byte_range(device, backup_file, start, end):
    #eprint("backup_byte_range()")
    if not start:
        start = int(backup_file.split('start_')[1].split('_')[0])
    #eprint("start:", start)
    if not end:
        end = int(backup_file.split('end_')[1].split('_')[0].split('.')[0])
    #eprint("end:", end)
    assert isinstance(start, int)
    assert isinstance(end, int)
    current_copy = backup_byte_range(device, start, end, note='current')
    #eprint("current_copy:", current_copy)
    #eprint("bakckup_file:", backup_file)
    vbindiff_command = "vbindiff " + current_copy + ' ' + backup_file
    eprint(vbindiff_command)
    os.system(vbindiff_command)

@click.command()
@click.option('--device',      is_flag=False, required=True)
@click.option('--backup-file', is_flag=False, required=True)
@click.option('--start',       is_flag=False, required=False, type=int)
@click.option('--end',         is_flag=False, required=False, type=int)
def main(device, backup_file, start, end):
    compare_byte_range(device, backup_file, start, end)

if __name__ == '__main__':
    main()
