#!/usr/bin/env python3

import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.printops import eprint
from .destroy_block_device_head_and_tail import destroy_block_device_head_and_tail
from kcl.deviceops import warn


def destroy_block_devices_head_and_tail(devices, size, note, force, no_backup):
    for device in devices:
        assert isinstance(no_backup, bool)
        assert not device[-1].isdigit()
        eprint("destroying device:", device)
        assert path_is_block_special(device)
        assert not block_special_path_is_mounted(device)

    if not force:
        warn(devices)

    for device in devices:
        destroy_block_device_head_and_tail(device, size, note, force, no_backup)


@click.command()
@click.argument('devices', required=True, nargs=-1)
@click.option('--size',   is_flag=False, required=False, type=int, default=(1024*1024*128))
@click.option('--note',   is_flag=False, required=False)
@click.option('--force',  is_flag=True,  required=False)
@click.option('--no-backup', is_flag=True,  required=False)
def main(devices, size, note, force, no_backup):
    destroy_block_device_head_and_tail(devices, size, note, force, no_backup)


if __name__ == '__main__':
    main()
