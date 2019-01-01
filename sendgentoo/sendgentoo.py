#!/usr/bin/env python3

import click
import os
import psutil
import sys
import pathlib
from .pre_chroot import pre_chroot


@click.command()
@click.argument("device")
@click.argument("ip")
def sendgentoo(device, ip):
    device = device.strip()
    if not os.getenv('TMUX'):
        print("Start a Tmux session first. Exiting.", file=sys.stderr)
        quit(1)

    partitions = psutil.disk_partitions()
    for partition in partitions:
        if device in partition.device:
            print("device:", device, "was found in:", partition.device, file=sys.stderr)
            print("Refusing to operate on mounted device. Exiting.", file=sys.stderr)
            quit(1)

    if not pathlib.Path(device).is_block_device():
            print("device:", device, "is not a block device. Exiting.", file=sys.stderr)

    password = input("Enter new password:")
    assert len(password) > 0

    pre_chroot()



if __name__ == '__main__':
    sendgentoo()
