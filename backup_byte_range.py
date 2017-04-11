#!/usr/bin/env python3
import os
import click
from kcl.timeops import timestamp

def backup_byte_range(device, start, end, note):
    #print("backup_byte_range()")
    with open(device, 'rb') as dfh:
        bytes_to_read = end - start
        assert bytes_to_read > 0
        dfh.seek(start)
        bytes_read = dfh.read(bytes_to_read)
        assert len(bytes_read) == bytes_to_read

    time_stamp = str(timestamp())
    running_on_hostname = os.uname()[1]
    device_string = device.replace('/', '_')
    backup_file_tail = '_.' + device_string + '.' + time_stamp + '.' + running_on_hostname +  '_start_' + str(start) + '_end_' + str(end) + '.bak'
    if note:
        backup_file = '_backup_' + note + backup_file_tail
    else:
        backup_file = '_backup__.' + backup_file_tail
    with open(backup_file, 'xb') as bfh:
        bfh.write(bytes_read)
    return backup_file

@click.command()
@click.option('--device', is_flag=False, required=True)
@click.option('--start',  is_flag=False, required=True, type=int)
@click.option('--end',    is_flag=False, required=True, type=int)
@click.option('--note',   is_flag=False, required=False, type=str)
def main(device, start, end, note):
    backup_file = backup_byte_range(device, start, end, note)
    print(backup_file)

if __name__ == '__main__':
    main()
    quit(0)


