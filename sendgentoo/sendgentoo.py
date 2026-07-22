#!/usr/bin/env python3

import os
import sys
from pathlib import Path

import click
import humanfriendly
from asserttool import ic
from boottool import create_boot_device
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_arch_select
from clicktool import click_global_options
from clicktool import tvicgvd
from clicktool.mesa import click_mesa_options
from devicetool import add_partition_number_to_device
from devicetool.cli import create_filesystem
from devicetool.cli import destroy_block_device_head_and_tail
from eprint import eprint
from globalverbose import gvd
from mounttool import path_is_mounted
from psutil import virtual_memory
from run_command import run_command
from sendgentoo_chroot import chroot_gentoo
from sendgentoo_chroot import rsync_cfg
from sendgentoo_stage import extract_stage3
from zfstool import create_zfs_filesystem
from zfstool import create_zfs_filesystem_snapshot
from zfstool import create_zfs_pool
from zfstool import zfs_check_mountpoints
from zfstool import zfs_set_sharenfs

from sendgentoo.create_root_device import create_root_device


def validate_ram_size(
    ctx: click.Context,
    param: click.Parameter,
    vm_ram: int | str,
) -> int:
    ic(vm_ram)
    if isinstance(vm_ram, int):
        vm_ram_bytes = vm_ram
    else:
        vm_ram_bytes = humanfriendly.parse_size(vm_ram)
    sysram_bytes = virtual_memory().total
    if vm_ram_bytes >= sysram_bytes:
        sysram_human = humanfriendly.format_size(sysram_bytes)
        vm_ram_human = humanfriendly.format_size(vm_ram_bytes)
        raise click.BadParameter(
            f"You entered {vm_ram_human} for --vm-ram but the host system only has {sysram_human}. Exiting."
        )
    return vm_ram_bytes


@click.group(no_args_is_help=True, cls=AHGroup)
@click.pass_context
def sendgentoo(ctx: click.Context) -> None:
    pass


sendgentoo.add_command(create_filesystem)
sendgentoo.add_command(create_zfs_pool)
sendgentoo.add_command(create_zfs_filesystem)
sendgentoo.add_command(create_zfs_filesystem_snapshot)
sendgentoo.add_command(create_root_device)
sendgentoo.add_command(chroot_gentoo)
sendgentoo.add_command(rsync_cfg)
sendgentoo.add_command(zfs_set_sharenfs)
sendgentoo.add_command(zfs_check_mountpoints)


def mount_filesystems(
    *,
    boot_device: Path,
    boot_filesystem: str,
    root_partition_path: Path,
    mount_path: Path,
) -> None:
    mount_path_boot = mount_path / "boot"
    mount_path_boot_efi = mount_path_boot / "efi"

    os.makedirs(mount_path, exist_ok=True)
    run_command(f"mount {root_partition_path.as_posix()} {mount_path.as_posix()}")
    assert path_is_mounted(mount_path)

    os.makedirs(mount_path_boot, exist_ok=True)
    assert not path_is_mounted(mount_path_boot)

    os.makedirs(mount_path_boot_efi, exist_ok=True)
    efi_partition_number = 9 if boot_filesystem == "zfs" else 2
    efi_partition_path = add_partition_number_to_device(
        device=boot_device,
        partition_number=efi_partition_number,
    )
    run_command(
        f"mount {efi_partition_path.as_posix()} {mount_path_boot_efi.as_posix()}"
    )
    assert path_is_mounted(mount_path_boot_efi)


@sendgentoo.command()
@click.argument(
    "root_devices",
    required=False,
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
    "--vm",
    is_flag=False,
    required=False,
    type=click.Choice(["qemu"]),
)
@click.option(
    "--vm-ram",
    is_flag=False,
    required=False,
    type=int,
    callback=validate_ram_size,
    default=1024**3,
)
@click.option(
    "--boot-device",
    is_flag=False,
    required=True,
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@click.option(
    "--boot-device-partition-table",
    is_flag=False,
    required=False,
    type=click.Choice(["gpt"]),
    default="gpt",
)
@click.option(
    "--root-device-partition-table",
    is_flag=False,
    required=False,
    type=click.Choice(["gpt"]),
    default="gpt",
)
@click.option(
    "--boot-filesystem",
    is_flag=False,
    required=False,
    type=click.Choice(["ext4", "zfs"]),
    default="ext4",
)
@click.option(
    "--root-filesystem",
    is_flag=False,
    required=True,
    type=click.Choice(["ext4", "zfs", "9p"]),
    default="ext4",
)
@click.option(
    "--stdlib",
    is_flag=False,
    required=True,
    type=click.Choice(["glibc", "musl"]),
)
@click.option(
    "--raid",
    is_flag=False,
    required=False,
    type=click.Choice(
        [
            "disk",
            "mirror",
            "raidz1",
            "raidz2",
            "raidz3",
            "raidz10",
            "raidz50",
            "raidz60",
        ]
    ),
    default="disk",
)
@click.option(
    "--raid-group-size",
    is_flag=False,
    required=False,
    type=click.IntRange(1, 2),
    default=1,
)
@click.option(
    "--march",
    is_flag=False,
    required=True,
    type=click.Choice(["native", "nocona"]),
)
@click.option(
    "--kernel",
    is_flag=False,
    required=True,
    type=click.Choice(["gentoo-sources", "pinebookpro-manjaro-sources"]),
    default="gentoo-sources",
)
@click.option("--hostname", is_flag=False, required=True)
@click.option("--newpasswd", is_flag=False, required=True)
@click.option("--ip", is_flag=False, required=True)
@click.option("--ip-gateway", is_flag=False, required=True)
@click.option("--proxy", is_flag=False, required=True)
@click.option("--force", is_flag=True, required=False)
@click.option("--pinebook-overlay", is_flag=True, required=False)
@click.option("--encrypt", is_flag=True, required=False)
@click.option("--multilib", is_flag=True, required=False)
@click.option("--minimal", is_flag=True, required=False)
@click.option("--skip-to-rsync", is_flag=True, required=False)
@click.option("--skip-to-chroot", is_flag=True, required=False)
@click.option("--configure-kernel", is_flag=True)
@click.option("--disk-size", type=str)
@click_add_options(click_mesa_options)
@click_add_options(click_arch_select)
@click_add_options(click_global_options)
@click.pass_context
def install(
    ctx: click.Context,
    *,
    root_devices: tuple[Path, ...],
    vm: None | str,
    vm_ram: int,
    boot_device: Path,
    boot_device_partition_table: str,
    root_device_partition_table: str,
    boot_filesystem: str,
    root_filesystem: str,
    stdlib: str,
    arch: str,
    raid: str,
    raid_group_size: int,
    march: str,
    hostname: str,
    newpasswd: str,
    disk_size: None | str,
    ip: str,
    ip_gateway: str,
    mesa_use_enable: list[str],
    mesa_use_disable: list[str],
    proxy: str,
    force: bool,
    encrypt: bool,
    configure_kernel: bool,
    pinebook_overlay: bool,
    kernel: str,
    multilib: bool,
    minimal: bool,
    verbose_inf: bool,
    dict_output: bool,
    skip_to_rsync: bool,
    skip_to_chroot: bool,
    verbose: bool = False,
) -> None:
    tty, verbose = tvicgvd(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
        ic=ic,
        gvd=gvd,
    )

    assert arch
    if skip_to_chroot:
        raise NotImplementedError("--skip-to-chroot")
    assert hostname.lower() == hostname
    assert "_" not in hostname

    mount_path = Path("/mnt/gentoo")

    if not skip_to_rsync:
        distfiles_dir = Path("/var/db/repos/gentoo/distfiles")
        os.makedirs(distfiles_dir, exist_ok=True)

        if not Path("/var/db/repos/gentoo/sys-kernel").is_dir():
            eprint("run emerge --sync first")
            sys.exit(1)
        if encrypt:
            eprint("encryption not yet supported")
            sys.exit(1)

        assert Path("/usr/bin/ischroot").exists()
        eprint("using C library:", stdlib)
        eprint("hostname:", hostname)

        if root_filesystem == "9p":
            assert vm

        if vm:
            assert vm_ram
            assert root_filesystem == "9p"
            assert not root_devices
            assert not boot_device
            assert not boot_filesystem
            guests_root = Path("/guests") / vm
            guest_path = guests_root / hostname
            guest_path_chroot = guests_root / (hostname + "-chroot")
            os.makedirs(guest_path, exist_ok=True)
            os.makedirs(guest_path_chroot, exist_ok=True)
            mount_path = guest_path
        else:
            assert boot_device
            assert root_devices

        if boot_device:
            assert boot_device_partition_table
            assert boot_filesystem

        if root_devices:
            assert root_device_partition_table

        if len(root_devices) > 1:
            assert root_filesystem == "zfs"
        elif len(root_devices) == 1:
            if root_filesystem == "zfs":
                assert raid == "disk"

        if root_filesystem == "zfs":
            assert root_device_partition_table == "gpt"

        if root_filesystem == "zfs" or boot_filesystem == "zfs":
            input(
                "note zfs boot/root is not working, many fixes will be needed, press enter to break things"
            )

        safety_check_devices(
            boot_device=boot_device,
            root_devices=root_devices,
            boot_device_partition_table=boot_device_partition_table,
            boot_filesystem=boot_filesystem,
            root_device_partition_table=root_device_partition_table,
            root_filesystem=root_filesystem,
            force=force,
            disk_size=disk_size,
        )

        if boot_device and root_devices and not vm:
            if boot_device == root_devices[0]:
                assert boot_filesystem == root_filesystem
                assert boot_device_partition_table == root_device_partition_table
                if boot_filesystem == "ext4":
                    ctx.invoke(
                        destroy_block_device_head_and_tail,
                        device=boot_device,
                        force=True,
                    )
                    create_boot_device(
                        ctx,
                        device=boot_device,
                        partition_table=boot_device_partition_table,
                        filesystem=boot_filesystem,
                        force=True,
                    )
                    ctx.invoke(
                        create_root_device,
                        devices=root_devices,
                        filesystem=root_filesystem,
                        partition_table=root_device_partition_table,
                        force=True,
                        raid=raid,
                        raid_group_size=raid_group_size,
                        pool_name=hostname,
                    )
                    root_partition_path = add_partition_number_to_device(
                        device=root_devices[0],
                        partition_number=3,
                    )
                elif boot_filesystem == "zfs":
                    raise NotImplementedError("zfs boot/root")
                else:
                    raise ValueError(f"unhandled boot_filesystem: {boot_filesystem}")
            else:
                raise NotImplementedError("separate boot and root devices")

            mount_filesystems(
                mount_path=mount_path,
                boot_device=boot_device,
                boot_filesystem=boot_filesystem,
                root_partition_path=root_partition_path,
            )

        extract_stage3(
            stdlib=stdlib,
            arch=arch,
            destination=mount_path,
            expect_mounted_destination=True,
            vm=vm,
            vm_ram=vm_ram,
        )

    assert boot_device
    ctx.invoke(
        chroot_gentoo,
        mount_path=mount_path,
        stdlib=stdlib,
        boot_device=boot_device,
        hostname=hostname,
        march=march,
        arch=arch,
        root_filesystem=root_filesystem,
        newpasswd=newpasswd,
        kernel=kernel,
        ip=ip,
        ip_gateway=ip_gateway,
        vm=vm,
        mesa_use_enable=mesa_use_enable,
        mesa_use_disable=mesa_use_disable,
        pinebook_overlay=pinebook_overlay,
        ipython=False,
        skip_to_rsync=skip_to_rsync,
        configure_kernel=configure_kernel,
        verbose=verbose,
        verbose_inf=verbose_inf,
        dict_output=dict_output,
    )


@sendgentoo.command()
@click.argument(
    "root_devices",
    required=False,
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
    "--boot-device",
    is_flag=False,
    required=True,
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        allow_dash=False,
        path_type=Path,
    ),
)
@click.option(
    "--boot-filesystem",
    is_flag=False,
    required=False,
    type=click.Choice(["ext4", "zfs"]),
    default="ext4",
)
@click.option(
    "--root-filesystem",
    is_flag=False,
    required=True,
    type=click.Choice(["ext4", "zfs", "9p"]),
    default="ext4",
)
@click_add_options(click_global_options)
@click.pass_context
def mount_existing_filesystems(
    ctx: click.Context,
    *,
    root_devices: tuple[Path, ...],
    boot_device: Path,
    boot_filesystem: str,
    root_filesystem: str,
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

    assert root_devices
    mount_path = Path("/mnt/gentoo")

    if boot_filesystem == root_filesystem == "ext4":
        root_partition_path = add_partition_number_to_device(
            device=root_devices[0],
            partition_number=3,
        )
    else:
        raise NotImplementedError(
            f"boot_filesystem={boot_filesystem} root_filesystem={root_filesystem}"
        )

    mount_filesystems(
        mount_path=mount_path,
        boot_device=boot_device,
        boot_filesystem=boot_filesystem,
        root_partition_path=root_partition_path,
    )
