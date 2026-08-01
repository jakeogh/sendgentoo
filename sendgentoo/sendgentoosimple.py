#!/usr/bin/env python3

import os
import sys
from pathlib import Path

import click
import psutil
from clicktool import click_add_options
from clicktool import click_global_options
from eprint import eprint

from sendgentoo.sendgentoo import install


@click.command()
@click.argument(
    "device",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@click.option("--hostname", type=str, required=True)
@click.option("--ip", type=str, required=True)
@click.option("--distfiles-url", type=str, required=True)
@click.option("--stage3-url", type=str, required=True)
@click.option("--root-password-hash", type=str, required=False, default=None)
@click.option("--stage3-keys-url", type=str, required=True)
@click.option("--disk-size", type=str)
@click.option("--full-disk", is_flag=True)
@click.option("--skip-to-chroot", is_flag=True)
@click.option("--configure-kernel", is_flag=True)
@click_add_options(click_global_options)
@click.pass_context
def sendgentoosimple(
    ctx: click.Context,
    *,
    device: Path,
    hostname: str,
    ip: str,
    root_password_hash: None | str,
    distfiles_url: str,
    stage3_url: str,
    stage3_keys_url: str,
    skip_to_chroot: bool,
    disk_size: None | str,
    full_disk: bool,
    configure_kernel: bool,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
) -> None:
    if not os.getenv("TMUX"):
        eprint("Start a tmux session first. Exiting.")
        sys.exit(1)

    if os.geteuid() != 0:
        eprint("You need to be root. Exiting.")
        sys.exit(1)

    if not skip_to_chroot:
        for partition in psutil.disk_partitions():
            if device.as_posix() in partition.device:
                eprint(
                    "device:",
                    device.as_posix(),
                    "was found:",
                    partition.device,
                    "mounted at:",
                    partition.mountpoint,
                )
                eprint("Refusing to operate on mounted device. Exiting.")
                sys.exit(1)

    if not device.is_block_device():
        eprint("device:", device.as_posix(), "is not a block device. Exiting.")
        sys.exit(1)

    ctx.invoke(
        install,
        root_devices=(device,),
        boot_device=device,
        boot_device_partition_table="gpt",
        root_device_partition_table="gpt",
        boot_filesystem="ext4",
        root_filesystem="ext4",
        stdlib="glibc",
        raid="disk",
        raid_group_size=1,
        arch="amd64",
        hostname=hostname,
        ip=ip,
        root_password_hash=root_password_hash,
        distfiles_url=distfiles_url,
        stage3_url=stage3_url,
        stage3_keys_url=stage3_keys_url,
        skip_to_chroot=skip_to_chroot,
        force=False,
        encrypt=False,
        multilib=False,
        configure_kernel=configure_kernel,
        disk_size=disk_size,
        full_disk=full_disk,
        verbose=verbose,
        verbose_inf=verbose_inf,
        dict_output=dict_output,
    )
