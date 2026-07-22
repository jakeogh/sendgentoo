#!/usr/bin/env python3

import sys
import time
from pathlib import Path

import click
import hs
from asserttool import ic
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tvicgvd
from devicetool import add_partition_number_to_device
from devicetool import path_is_block_special
from globalverbose import gvd
from mounttool import block_special_path_is_mounted
from warntool import warn
from zfstool import RAID_LIST


@click.command()
@click.argument(
    "devices",
    required=True,
    nargs=-1,
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@click.option(
    "--filesystem",
    is_flag=False,
    required=True,
    type=click.Choice(["ext4", "zfs", "fat32"]),
)
@click.option("--force", is_flag=True, required=False)
@click.option("--exclusive", is_flag=True, required=False)
@click.option(
    "--raid",
    is_flag=False,
    required=True,
    type=click.Choice(RAID_LIST),
)
@click.option(
    "--raid-group-size",
    is_flag=False,
    required=True,
    type=int,
)
@click.option("--pool-name", is_flag=False, type=str)
@click_add_options(click_global_options)
@click.pass_context
def write_sysfs_partition(
    ctx: click.Context,
    *,
    devices: tuple[Path, ...],
    filesystem: str,
    force: bool,
    exclusive: bool,
    raid: str,
    raid_group_size: int,
    pool_name: None | str,
    verbose_inf: bool,
    dict_output: bool,
    verbose: bool = False,
) -> None:
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    ic("creating sysfs partition on:", devices)

    if filesystem == "zfs":
        assert pool_name

    for _device in devices:
        if not _device.name.startswith("nvme"):
            assert not _device.name[-1].isdigit()
        assert path_is_block_special(_device, symlink_ok=True)
        assert not block_special_path_is_mounted(_device)

    if not force:
        warn(devices, symlink_ok=True)

    if filesystem == "zfs":
        assert exclusive
        raise NotImplementedError("zfs root")

    assert len(devices) == 1
    device = devices[0]
    if exclusive:
        partition_number = 1
        start = "0%"
    else:
        partition_number = 3
        start = "100MiB"

    parted = hs.Command("parted")
    parted(
        "-a",
        "optimal",
        device.as_posix(),
        "--script",
        "--",
        "mkpart",
        "primary",
        filesystem,
        start,
        "100%",
        _out=sys.stdout,
        _err=sys.stderr,
    )
    parted(
        device.as_posix(),
        "--script",
        "--",
        "name",
        str(partition_number),
        "rootfs",
        _out=sys.stdout,
        _err=sys.stderr,
    )
    time.sleep(1)
    sysfs_partition_path = add_partition_number_to_device(
        device=device,
        partition_number=partition_number,
    )
    mkfs = {"ext4": "mkfs.ext4", "fat32": "mkfs.vfat"}[filesystem]
    hs.Command(mkfs)(sysfs_partition_path.as_posix(), _out=sys.stdout, _err=sys.stderr)
