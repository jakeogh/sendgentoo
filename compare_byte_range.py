#!/usr/bin/env python3
import sys
import click
#import time
#from kcl.time import timestamp
import os
from backup_byte_range import backup_byte_range

def compare_byte_range(device, backup_file, start, end):
    #print("backup_byte_range()")
    if not start:
        start = int(backup_file.split('start_')[1].split('_')[0])
    #print("start:", start, file=sys.stderr)
    if not end:
        end = int(backup_file.split('end_')[1].split('_')[0].split('.')[0])
    #print("end:", end, file=sys.stderr)
    assert isinstance(start, int)
    assert isinstance(end, int)
    current_copy = backup_byte_range(device, start, end, note='current')
    #print("current_copy:", current_copy, file=sys.stderr)
    #print("bakckup_file:", backup_file, file=sys.stderr)
    vbindiff_command = "vbindiff " + current_copy + ' ' + backup_file
    print(vbindiff_command, file=sys.stderr)
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
    quit(0)


