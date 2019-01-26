#!/usr/bin/env python3

import click
import time
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.printops import eprint
from .warn import warn


def destroy_block_device_ask(device, force):
    assert not device[-1].isdigit()
    eprint("destroying device:", device)
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)
    if not force:
        warn((device,))
    wipe_command = "dd if=/dev/urandom of=" + device
    print(wipe_command)


@click.command()
@click.argument('device', required=True, nargs=1)
@click.option('--force', is_flag=True, required=False)
def main(device, force):
    destroy_block_device_ask(device=device, force=force)


if __name__ == '__main__':
    main()
