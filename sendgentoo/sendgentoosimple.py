#!/usr/bin/env python3

import os
import pathlib
import sys

import click
import psutil

from .sendgentoo import install


@click.command()
@click.argument("device")
@click.option("--hostname", type=str, required=True)
@click.option("--ip", type=str, required=True)
@click.option("--skip-to-chroot", if_flag=True)
@click.pass_context
def sendgentoosimple(ctx,
                     device: str,
                     hostname: str,
                     ip: str,
                     skip_to_chroot: bool,
                     ):

    device = device.strip()
    if not os.getenv('TMUX'):
        print("Start a Tmux session first. Exiting.", file=sys.stderr)
        quit(1)

    if not os.geteuid() == 0:
        print("you ned to be root. Exiting.", file=sys.stderr)
        quit(1)

    partitions = psutil.disk_partitions()
    for partition in partitions:
        if device in partition.device:
            print("device:", device, "was found:", partition.device, "mounted at:", partition.mountpoint, file=sys.stderr)
            print("Refusing to operate on mounted device. Exiting.", file=sys.stderr)
            quit(1)

    if not pathlib.Path(device).is_block_device():
            print("device:", device, "is not a block device. Exiting.", file=sys.stderr)
            quit(1)

    password = input("Enter new password: ")
    assert len(password) > 0

    ctx.invoke(install,
               root_devices=(device,),
               boot_device=device,
               boot_device_partition_table='gpt',
               root_device_partition_table='gpt',
               boot_filesystem='ext4',
               root_filesystem='ext4',
               stdlib='glibc',
               raid='disk',
               raid_group_size='1',
               march='nocona',
               hostname=hostname,
               newpasswd=password,
               ip=ip,
               skip_to_chroot=skip_to_chroot,
               force=False,
               encrypt=False,
               multilib=False,)

