#!/usr/bin/env python3

# flake8: noqa
# pylint: disable=missing-docstring               # [C0111] docstrings are always outdated and wrong
# pylint: disable=fixme                           # [W0511] todo is encouraged
# pylint: disable=line-too-long                   # [C0301]
# pylint: disable=too-many-instance-attributes    # [R0902]
# pylint: disable=too-many-lines                  # [C0302] too many lines in module
# pylint: disable=invalid-name                    # [C0103] single letter var names, name too descriptive
# pylint: disable=too-many-return-statements      # [R0911]
# pylint: disable=too-many-branches               # [R0912]
# pylint: disable=too-many-statements             # [R0915]
# pylint: disable=too-many-arguments              # [R0913]
# pylint: disable=too-many-nested-blocks          # [R1702]
# pylint: disable=too-many-locals                 # [R0914]
# pylint: disable=too-few-public-methods          # [R0903]
# pylint: disable=no-member                       # [E1101] no member for base
# pylint: disable=attribute-defined-outside-init  # [W0201]
# pylint: disable=too-many-boolean-expressions    # [R0916] in if statement
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Tuple

import click
import humanfriendly
from asserttool import ic
from asserttool import root_user
from boottool import create_boot_device
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_arch_select
from clicktool import click_global_options
from clicktool.mesa import click_mesa_options
from compile_kernel.compile_kernel import kcompile
from devicetool import add_partition_number_to_device
from devicetool import create_filesystem
from devicetool import destroy_block_device_head_and_tail
from devicetool import device_is_not_a_partition
from devicetool import path_is_block_special
from devicetool import safety_check_devices
from eprint import eprint
from mounttool import block_special_path_is_mounted
from mounttool import path_is_mounted
from psutil import virtual_memory
from run_command import run_command
from sendgentoo.create_root_device import create_root_device
from sendgentoo_chroot import chroot_gentoo
from sendgentoo_chroot import rsync_cfg
from sendgentoo_stage import extract_stage3
from warntool import warn
from zfstool import create_zfs_filesystem
from zfstool import create_zfs_filesystem_snapshot
from zfstool import create_zfs_pool
from zfstool import zfs_check_mountpoints
from zfstool import zfs_set_sharenfs


def validate_ram_size(ctx, param, vm_ram):
    ic(vm_ram)
    sysram_bytes = virtual_memory().total
    if not isinstance(vm_ram, int):
        vm_ram_bytes = humanfriendly.parse_size(vm_ram)
    else:
        vm_ram_bytes = vm_ram
    if vm_ram_bytes >= sysram_bytes:
        sysram_human = humanfriendly.format_size(sysram_bytes)
        vm_ram_human = humanfriendly.format_size(vm_ram_bytes)
        raise click.BadParameter(
            f"You entered {vm_ram_human} for --vm-ram but the host system only has {sysram_human}. Exiting."
        )
    return vm_ram_bytes


@click.group(no_args_is_help=True, cls=AHGroup)
@click.pass_context
def sendgentoo(ctx):
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


@sendgentoo.command()
@click.option(
    "--boot-device",
    is_flag=False,
    required=True,
    type=click.Path(exists=True, path_type=Path),
)
@click.option("--force", is_flag=True, required=False)
@click.option("--no-configure-kernel", is_flag=True, required=False)
@click_add_options(click_global_options)
@click.pass_context
def compile_kernel(
    ctx,
    *,
    boot_device: Path,
    no_configure_kernel: bool,
    force: bool,
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
):

    if not root_user():
        ic("You must be root.")
        sys.exit(1)

    configure_kernel = not no_configure_kernel

    mount_path_boot = Path("/boot")
    ic(mount_path_boot)
    assert not path_is_mounted(
        mount_path_boot,
        verbose=verbose,
    )

    mount_path_boot_efi = mount_path_boot / Path("efi")
    ic(mount_path_boot_efi)
    assert not path_is_mounted(
        mount_path_boot_efi,
        verbose=verbose,
    )

    assert device_is_not_a_partition(
        device=boot_device,
        verbose=verbose,
    )

    assert path_is_block_special(boot_device)
    assert not block_special_path_is_mounted(
        boot_device,
        verbose=verbose,
    )
    warn(
        (boot_device,),
        msg="about to update the kernel on device:",
        verbose=verbose,
    )

    os.makedirs(mount_path_boot, exist_ok=True)
    os.makedirs(mount_path_boot / Path("grub"), exist_ok=True)
    boot_partition_path = add_partition_number_to_device(
        device=boot_device,
        partition_number=3,
        verbose=verbose,
    )
    boot_mount_command = "mount " + boot_partition_path + " " + str(mount_path_boot)
    assert not path_is_mounted(
        mount_path_boot,
        verbose=verbose,
    )
    run_command(boot_mount_command, verbose=True, popen=True)
    assert path_is_mounted(
        mount_path_boot,
        verbose=verbose,
    )

    os.makedirs(mount_path_boot_efi, exist_ok=True)

    efi_partition_path = add_partition_number_to_device(
        device=boot_device,
        partition_number=2,
        verbose=verbose,
    )
    efi_mount_command = "mount " + efi_partition_path + " " + str(mount_path_boot_efi)
    assert not path_is_mounted(
        mount_path_boot_efi,
        verbose=verbose,
    )
    run_command(efi_mount_command, verbose=True, popen=True)
    assert path_is_mounted(
        mount_path_boot_efi,
        verbose=verbose,
    )

    kcompile(
        configure=configure_kernel,
        configure_only=False,
        force=force,
        no_check_boot=True,
        verbose=verbose,
    )

    grub_config_command = "grub-mkconfig -o /boot/grub/grub.cfg"
    run_command(grub_config_command, verbose=True, popen=True)


@sendgentoo.command()
@click.argument(
    "root_devices", required=False, nargs=-1
)  # --vm does not need a specified root device
@click.option("--vm", is_flag=False, required=False, type=click.Choice(["qemu"]))
@click.option(
    "--vm-ram",
    is_flag=False,
    required=False,
    type=int,
    callback=validate_ram_size,
    default=1024**3,
)
@click.option("--boot-device", is_flag=False, required=True)
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
    type=click.Choice(["glibc", "musl", "uclibc"]),
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
    "--march", is_flag=False, required=True, type=click.Choice(["native", "nocona"])
)
@click.option(
    "--kernel",
    is_flag=False,
    required=True,
    type=click.Choice(["gentoo-sources", "pinebookpro-manjaro-sources"]),
    default="gentoo-sources",
)
# @click.option('--pool-name',                   is_flag=False, required=True, type=str)
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
@click_add_options(click_mesa_options)
@click_add_options(click_arch_select)
@click_add_options(click_global_options)
@click.pass_context
def install(
    ctx,
    *,
    root_devices: Tuple[Path, ...],
    vm: str,
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
    ip: str,
    ip_gateway: str,
    mesa_use_enable: list[str],
    mesa_use_disable: list[str],
    proxy: str,
    force: bool,
    encrypt: bool,
    pinebook_overlay: bool,
    kernel: str,
    multilib: bool,
    minimal: bool,
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
    skip_to_rsync: bool,
):

    assert isinstance(root_devices, tuple)
    boot_device = Path(boot_device)
    root_devices = tuple([Path(_device) for _device in root_devices])
    assert isinstance(root_devices, tuple)
    assert hostname.lower() == hostname
    assert "_" not in hostname

    mount_path = Path("/mnt/gentoo")
    mount_path_boot = mount_path / Path("boot")
    mount_path_boot_efi = mount_path_boot / Path("efi")

    if not skip_to_rsync:
        distfiles_dir = Path("/var/db/repos/gentoo/distfiles")
        os.makedirs(distfiles_dir, exist_ok=True)

        if not os.path.isdir("/var/db/repos/gentoo/sys-kernel"):
            eprint("run emerge --sync first")
            sys.exit(1)
        if encrypt:
            eprint("encryption not yet supported")
            # sys.exit(1)
        if stdlib == "uclibc":
            eprint(
                "uclibc fails with efi grub because efivar fails to compile. See Note."
            )
            sys.exit(1)

        os.makedirs(mount_path, exist_ok=True)

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
            guests_root = Path("/guests") / Path(vm)
            guest_path = guests_root / Path(hostname)
            guest_path_chroot = guests_root / Path(hostname + "-chroot")
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
            verbose=verbose,
            boot_device_partition_table=boot_device_partition_table,
            boot_filesystem=boot_filesystem,
            root_device_partition_table=root_device_partition_table,
            root_filesystem=root_filesystem,
            force=force,
        )

        if boot_device and root_devices and not vm:
            if boot_device == root_devices[0]:
                assert boot_filesystem == root_filesystem
                assert boot_device_partition_table == root_device_partition_table
                if boot_filesystem == "zfs":
                    assert False
                    # untested
                    # ctx.invoke(destroy_block_devices_head_and_tail,
                    #           devices=root_devices,
                    #           force=True,
                    #           no_backup=True,
                    #           size=(1024 * 1024 * 128),
                    #           note=False,
                    #           verbose=verbose,
                    #           )
                    ## if this is zfs, it will make a gpt table, / and EFI partition
                    # ctx.invoke(create_root_device,
                    #           devices=root_devices,
                    #           exclusive=True,
                    #           filesystem=root_filesystem,
                    #           partition_table=root_device_partition_table,
                    #           force=True,
                    #           raid=raid,
                    #           raid_group_size=raid_group_size,
                    #           pool_name=hostname,)
                    # create_boot_device(ctx,
                    #                   device=boot_device,
                    #                   partition_table='none',
                    #                   filesystem=boot_filesystem,
                    #                   force=True,
                    #                   verbose=verbose,
                    #                   )  # dont want to delete the gpt that zfs made
                    # boot_mount_command = False
                    # root_mount_command = False

                elif boot_filesystem == "ext4":
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
                        verbose=verbose,
                    )  # writes gurb_bios from 48s to 1023s then writes EFI partition from 1024s to 205824s (100M efi) (nope, too big for fat16)
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
                        verbose=verbose,
                    )
                    root_mount_command = (
                        "mount "
                        + root_partition_path.as_posix()
                        + " "
                        + str(mount_path)
                    )
                    boot_mount_command = False
                else:  # unknown case
                    assert False
            else:
                assert False
                # not tested
                # eprint("differing root and boot devices: (exclusive) root_devices[0]:", root_devices[0], "boot_device:", boot_device)
                # create_boot_device(ctx,
                #                   device=boot_device,
                #                   partition_table=boot_device_partition_table,
                #                   filesystem=boot_filesystem,
                #                   force=True,
                #                   verbose=verbose,
                #                   )
                # ctx.invoke(write_boot_partition,
                #           device=boot_device,
                #           force=True,
                #           verbose=verbose,
                #           )
                # ctx.invoke(create_root_device,
                #           devices=root_devices,
                #           exclusive=True,
                #           filesystem=root_filesystem,
                #           partition_table=root_device_partition_table,
                #           force=True,
                #           raid=raid,)
                # if root_filesystem == 'zfs':
                #    assert False
                #    root_mount_command = False
                # elif root_filesystem == 'ext4':
                #    root_partition_path = add_partition_number_to_device(device=root_devices[0], partition_number="1")
                #    root_mount_command = "mount " + root_partition_path.as_posix() + " " + mount_path.as_posix()

                # boot_partition_path = add_partition_number_to_device(device=boot_device, partition_number="3")
                # boot_mount_command = "mount " + boot_partition_path.as_posix() + " " + mount_path_boot.as_posix()

            if root_mount_command:
                run_command(
                    root_mount_command,
                    verbose=verbose,
                )

            assert path_is_mounted(
                mount_path,
                verbose=verbose,
            )

            os.makedirs(mount_path_boot, exist_ok=True)

            if boot_mount_command:
                run_command(
                    boot_mount_command,
                    verbose=verbose,
                )
                assert path_is_mounted(
                    mount_path_boot,
                    verbose=verbose,
                )
            else:
                assert not path_is_mounted(
                    mount_path_boot,
                    verbose=verbose,
                )

            if boot_device:
                os.makedirs(mount_path_boot_efi, exist_ok=True)

            if boot_filesystem == "zfs":
                efi_partition_path = add_partition_number_to_device(
                    device=boot_device,
                    partition_number=9,
                    verbose=verbose,
                )
                efi_mount_command = (
                    "mount "
                    + efi_partition_path.as_posix()
                    + " "
                    + mount_path_boot_efi.as_posix()
                )
            else:
                efi_partition_path = add_partition_number_to_device(
                    device=boot_device,
                    partition_number=2,
                    verbose=verbose,
                )
                efi_mount_command = (
                    "mount "
                    + efi_partition_path.as_posix()
                    + " "
                    + mount_path_boot_efi.as_posix()
                )

            if boot_device:
                run_command(
                    efi_mount_command,
                    verbose=verbose,
                )
                assert path_is_mounted(
                    mount_path_boot_efi,
                    verbose=verbose,
                )

        extract_stage3(
            stdlib=stdlib,
            multilib=multilib,
            arch=arch,
            destination=mount_path,
            expect_mounted_destination=True,
            vm=vm,
            vm_ram=vm_ram,
            verbose=verbose,
        )

    # skip_to_rsync lands here
    if not boot_device:
        assert False
        # boot_device = "False"  # fixme

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
        verbose=verbose,
        verbose_inf=verbose_inf,
        dict_output=dict_output,
    )
