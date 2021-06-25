#!/usr/bin/env python3

# flake8: noqa
# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=W0511  # todo is encouraged
# pylint: disable=C0301  # line too long
# pylint: disable=R0902  # too many instance attributes
# pylint: disable=C0302  # too many lines in module
# pylint: disable=C0103  # single letter var names, func name too descriptive
# pylint: disable=R0911  # too many return statements
# pylint: disable=R0912  # too many branches
# pylint: disable=R0915  # too many statements
# pylint: disable=R0913  # too many arguments
# pylint: disable=R1702  # too many nested blocks
# pylint: disable=R0914  # too many local variables
# pylint: disable=R0903  # too few public methods
# pylint: disable=E1101  # no member for base
# pylint: disable=W0201  # attribute defined outside __init__
# pylint: disable=R0916  # Too many boolean expressions in if statement
# pylint: disable=C0305  # Trailing newlines editor should fix automatically, pointless warning


import os
import sys
from pathlib import Path
from typing import Iterator
from typing import Tuple

import click
import humanfriendly
from asserttool import root_user
from blocktool import add_partition_number_to_device
from blocktool import create_filesystem
from blocktool import destroy_block_device_head_and_tail
from blocktool import destroy_block_devices_head_and_tail
from blocktool import device_is_not_a_partition
from blocktool import get_block_device_size
from blocktool import path_is_block_special
from blocktool import warn
from compile_kernel.compile_kernel import kcompile
from mounttool import block_special_path_is_mounted
from mounttool import path_is_mounted
from psutil import virtual_memory
from run_command import run_command

from sendgentoo.chroot_gentoo import chroot_gentoo
from sendgentoo.chroot_gentoo import rsync_cfg
from sendgentoo.create_boot_device import create_boot_device
from sendgentoo.create_root_device import create_root_device
from sendgentoo.create_zfs_filesystem import create_zfs_filesystem
from sendgentoo.create_zfs_pool import create_zfs_pool
from sendgentoo.install_stage3 import install_stage3
from sendgentoo.write_boot_partition import write_boot_partition


def eprint(*args, **kwargs):
    if 'file' in kwargs.keys():
        kwargs.pop('file')
    print(*args, file=sys.stderr, **kwargs)


try:
    from icecream import ic  # https://github.com/gruns/icecream
except ImportError:
    ic = eprint


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
        raise click.BadParameter('You entered {0} for --vm-ram but the host system only has {1}. Exiting.'.format(vm_ram_human, sysram_human))
    return vm_ram_bytes


@click.group()
@click.pass_context
def sendgentoo(ctx):
    pass


sendgentoo.add_command(create_filesystem)
sendgentoo.add_command(create_zfs_pool)
sendgentoo.add_command(create_zfs_filesystem)
sendgentoo.add_command(create_root_device)
sendgentoo.add_command(chroot_gentoo)
sendgentoo.add_command(rsync_cfg)


@sendgentoo.command()
@click.option('--boot-device',                 is_flag=False, required=True)
@click.option('--force',                       is_flag=True,  required=False)
@click.option('--no-configure-kernel',         is_flag=True,  required=False)
@click.option('--verbose',                     is_flag=True,  required=False)
@click.option('--debug',                       is_flag=True,  required=False)
@click.pass_context
def compile_kernel(ctx, *,
                   boot_device,
                   no_configure_kernel: bool,
                   force: bool,
                   verbose: bool,
                   debug: bool
                   ,):

    if not root_user():
        ic('You must be root.')
        sys.exit(1)

    configure_kernel = not no_configure_kernel

    mount_path_boot = Path('/boot')
    ic(mount_path_boot)
    assert not path_is_mounted(mount_path_boot, verbose=verbose, debug=debug,)

    mount_path_boot_efi = mount_path_boot / Path('efi')
    ic(mount_path_boot_efi)
    assert not path_is_mounted(mount_path_boot_efi, verbose=verbose, debug=debug,)

    assert device_is_not_a_partition(device=boot_device, verbose=verbose, debug=debug,)

    assert path_is_block_special(boot_device)
    assert not block_special_path_is_mounted(boot_device, verbose=verbose, debug=debug,)
    warn((boot_device,), msg="about to update the kernel on device:", verbose=verbose, debug=debug,)

    os.makedirs(mount_path_boot, exist_ok=True)
    boot_partition_path = add_partition_number_to_device(device=boot_device, partition_number="3")
    boot_mount_command = "mount " + boot_partition_path + " " + str(mount_path_boot)
    assert not path_is_mounted(mount_path_boot, verbose=verbose, debug=debug,)
    run_command(boot_mount_command, verbose=True, popen=True)
    assert path_is_mounted(mount_path_boot, verbose=verbose, debug=debug,)

    os.makedirs(mount_path_boot_efi, exist_ok=True)

    efi_partition_path = add_partition_number_to_device(device=boot_device, partition_number="2")
    efi_mount_command = "mount " + efi_partition_path + " " + str(mount_path_boot_efi)
    assert not path_is_mounted(mount_path_boot_efi, verbose=verbose, debug=debug,)
    run_command(efi_mount_command, verbose=True, popen=True)
    assert path_is_mounted(mount_path_boot_efi, verbose=verbose, debug=debug,)

    kcompile(configure=configure_kernel,
             force=force,
             no_check_boot=True,
             verbose=verbose,
             debug=debug)

    grub_config_command = "grub-mkconfig -o /boot/grub/grub.cfg"
    run_command(grub_config_command, verbose=True, popen=True)


@sendgentoo.command()
@click.option('--boot-device',                 is_flag=False, required=True)
@click.option('--boot-device-partition-table', is_flag=False, required=False, type=click.Choice(['gpt']), default="gpt")
@click.option('--boot-filesystem',             is_flag=False, required=False, type=click.Choice(['ext4']), default="ext4")
@click.option('--force',                       is_flag=True,  required=False)
@click.option('--compile-kernel', "_compile_kernel", is_flag=True, required=False)
@click.option('--configure-kernel',            is_flag=True,  required=False)
@click.option('--verbose',                     is_flag=True,  required=False)
@click.option('--debug',                       is_flag=True,  required=False)
@click.pass_context
def create_boot_device_for_existing_root(ctx,
                                         boot_device,
                                         boot_device_partition_table,
                                         boot_filesystem,
                                         _compile_kernel: bool,
                                         configure_kernel: bool,
                                         force: bool,
                                         verbose: bool,
                                         debug: bool,):
    if configure_kernel:
        _compile_kernel = True

    if not root_user():
        ic('You must be root.')
        sys.exit(1)

    mount_path_boot = Path('/boot')
    ic(mount_path_boot)
    assert not path_is_mounted(mount_path_boot, verbose=verbose, debug=debug,)

    mount_path_boot_efi = mount_path_boot / Path('efi')
    ic(mount_path_boot_efi)
    assert not path_is_mounted(mount_path_boot_efi, verbose=verbose, debug=debug,)

    assert device_is_not_a_partition(device=boot_device, verbose=verbose, debug=debug,)

    ic('installing grub on boot device:',
       boot_device,
       boot_device_partition_table,
       boot_filesystem)
    assert path_is_block_special(boot_device)
    assert not block_special_path_is_mounted(boot_device, verbose=verbose, debug=debug,)
    if not force:
        warn((boot_device,), verbose=verbose, debug=debug,)
    create_boot_device(ctx,
                       device=boot_device,
                       partition_table=boot_device_partition_table,
                       filesystem=boot_filesystem,
                       force=True,
                       verbose=verbose,
                       debug=debug,)
    ctx.invoke(write_boot_partition,
               device=boot_device,
               force=True,
               verbose=verbose,
               debug=debug,)

    hybrid_mbr_command = "/home/cfg/_myapps/sendgentoo/sendgentoo/gpart_make_hybrid_mbr.sh" + " " + boot_device
    run_command(hybrid_mbr_command, verbose=True, popen=True)

    os.makedirs(mount_path_boot, exist_ok=True)
    boot_partition_path = add_partition_number_to_device(device=boot_device, partition_number="3")
    boot_mount_command = "mount " + boot_partition_path + " " + str(mount_path_boot)
    #print("sleeping")
    #time.sleep(10)
    assert not path_is_mounted(mount_path_boot, verbose=verbose, debug=debug,)
    run_command(boot_mount_command, verbose=True, popen=True)
    assert path_is_mounted(mount_path_boot, verbose=verbose, debug=debug,)

    os.makedirs(mount_path_boot_efi, exist_ok=True)

    efi_partition_path = add_partition_number_to_device(device=boot_device, partition_number="2")
    efi_mount_command = "mount " + efi_partition_path + " " + str(mount_path_boot_efi)
    assert not path_is_mounted(mount_path_boot_efi, verbose=verbose, debug=debug,)
    run_command(efi_mount_command, verbose=True, popen=True)
    assert path_is_mounted(mount_path_boot_efi, verbose=verbose, debug=debug,)

    grub_install_command = "/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot_install_grub.sh" + " " + boot_device
    run_command(grub_install_command, verbose=True, popen=True)

    if _compile_kernel:
        kcompile(configure=configure_kernel,
                 force=force,
                 no_check_boot=True,
                 verbose=verbose,
                 debug=debug)

    grub_config_command = "grub-mkconfig -o /boot/grub/grub.cfg"
    run_command(grub_config_command, verbose=True, popen=True)


def safety_check_devices(boot_device: Path,
                         root_devices: Tuple[Path, ...],
                         verbose: bool,
                         debug: bool,
                         boot_device_partition_table: str,
                         boot_filesystem: str,
                         root_device_partition_table: str,
                         root_filesystem: str,
                         force: bool,
                         ):
    if boot_device:
        assert device_is_not_a_partition(device=boot_device,
                                         verbose=verbose,
                                         debug=debug,)

    for device in root_devices:
        assert device_is_not_a_partition(device=device,
                                         verbose=verbose,
                                         debug=debug,)

    if boot_device:
        eprint("installing gentoo on boot device: {boot_device} {boot_device_partition_table} {boot_filesystem}".format(boot_device=boot_device, boot_device_partition_table=boot_device_partition_table, boot_filesystem=boot_filesystem))
        assert path_is_block_special(boot_device)
        assert not block_special_path_is_mounted(boot_device, verbose=verbose, debug=debug,)

    if root_devices:
        eprint("installing gentoo on root device(s):", root_devices, '(' + root_device_partition_table + ')', '(' + root_filesystem + ')')
        for device in root_devices:
            assert path_is_block_special(device)
            assert not block_special_path_is_mounted(device, verbose=verbose, debug=debug,)

    for device in root_devices:
        eprint("boot_device:", boot_device)
        eprint("device:", device)
        eprint("get_block_device_size(boot_device):", get_block_device_size(boot_device, verbose=verbose, debug=debug,))
        eprint("get_block_device_size(device):     ", get_block_device_size(device, verbose=verbose, debug=debug,))
        assert get_block_device_size(boot_device, verbose=verbose, debug=debug,) <= get_block_device_size(device, verbose=verbose, debug=debug,)

    if root_devices:
        first_root_device_size = get_block_device_size(root_devices[0], verbose=verbose, debug=debug,)

        for device in root_devices:
            assert get_block_device_size(device, verbose=verbose, debug=debug,) == first_root_device_size

    if boot_device or root_devices:
        if not force:
            warn((boot_device,), verbose=verbose, debug=debug,)
            warn(root_devices, verbose=verbose, debug=debug,)


@sendgentoo.command()
@click.argument('root_devices',                required=False, nargs=-1)  # --vm does not need a specified root device
@click.option('--vm',                          is_flag=False, required=False, type=click.Choice(['qemu']))
@click.option('--vm-ram',                      is_flag=False, required=False, type=int, callback=validate_ram_size, default=1024**3)
@click.option('--boot-device',                 is_flag=False, required=True)
@click.option('--boot-device-partition-table', is_flag=False, required=False, type=click.Choice(['gpt']), default="gpt")
@click.option('--root-device-partition-table', is_flag=False, required=False, type=click.Choice(['gpt']), default="gpt")
@click.option('--boot-filesystem',             is_flag=False, required=False, type=click.Choice(['ext4', 'zfs']), default="ext4")
@click.option('--root-filesystem',             is_flag=False, required=True,  type=click.Choice(['ext4', 'zfs', '9p']), default="ext4")
@click.option('--stdlib',                      is_flag=False, required=False, type=click.Choice(['glibc', 'musl', 'uclibc']), default="glibc")
@click.option('--arch',                        is_flag=False, required=False, type=click.Choice(['alpha', 'amd64', 'arm', 'hppa', 'ia64', 'mips', 'ppc', 's390', 'sh', 'sparc', 'x86']), default="amd64")
@click.option('--raid',                        is_flag=False, required=False, type=click.Choice(['disk', 'mirror', 'raidz1', 'raidz2', 'raidz3', 'raidz10', 'raidz50', 'raidz60']), default="disk")
@click.option('--raid-group-size',             is_flag=False, required=False, type=click.IntRange(1, 2), default=1)
@click.option('--march',                       is_flag=False, required=True, type=click.Choice(['native', 'nocona']))
#@click.option('--pool-name',                   is_flag=False, required=True, type=str)
@click.option('--hostname',                    is_flag=False, required=True)
@click.option('--newpasswd',                   is_flag=False, required=True)
@click.option('--ip',                          is_flag=False, required=True)
@click.option('--ip-gateway',                  is_flag=False, required=True)
@click.option('--proxy',                       is_flag=False, required=True)
@click.option('--force',                       is_flag=True,  required=False)
@click.option('--encrypt',                     is_flag=True,  required=False)
@click.option('--multilib',                    is_flag=True,  required=False)
@click.option('--minimal',                     is_flag=True,  required=False)
@click.option('--verbose',                     is_flag=True,  required=False)
@click.option('--debug',                       is_flag=True,  required=False)
@click.pass_context
def install(ctx, *,
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
            proxy: str,
            force: bool,
            encrypt: bool,
            multilib: bool,
            minimal: bool,
            verbose: bool,
            debug: bool,
            ):

    assert isinstance(root_devices, tuple)
    boot_device = Path(boot_device)
    root_devices = tuple([Path(_device) for _device in root_devices])
    assert isinstance(root_devices, tuple)
    assert hostname.lower() == hostname
    assert '_' not in hostname

    distfiles_dir = Path('/var/db/repos/gentoo/distfiles')
    os.makedirs(distfiles_dir, exist_ok=True)

    if not os.path.isdir('/var/db/repos/gentoo/sys-kernel'):
        eprint("run emerge --sync first")
        sys.exit(1)
    if encrypt:
        eprint("encryption not yet supported")
        #sys.exit(1)
    if stdlib == 'musl':
        eprint("musl not yet supported")
        sys.exit(1)
    if stdlib == 'uclibc':
        eprint("uclibc fails with efi grub because efivar fails to compile. See Note.")
        sys.exit(1)

    mount_path = Path("/mnt/gentoo")
    mount_path_boot = mount_path / Path('boot')
    mount_path_boot_efi = mount_path_boot / Path('efi')

    os.makedirs(mount_path, exist_ok=True)

    assert Path('/usr/bin/ischroot').exists()
    eprint("using C library:", stdlib)
    eprint("hostname:", hostname)

    if root_filesystem == '9p':
        assert vm

    if vm:
        assert vm_ram
        assert root_filesystem == "9p"
        assert not root_devices
        assert not boot_device
        assert not boot_filesystem
        guests_root = Path('/guests') / Path(vm)
        guest_path        = guests_root / Path(hostname)
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
        assert root_filesystem == 'zfs'
    elif len(root_devices) == 1:
        if root_filesystem == 'zfs':
            assert raid == 'disk'

    if root_filesystem == 'zfs':
        assert root_device_partition_table == 'gpt'

    if root_filesystem == 'zfs' or boot_filesystem == 'zfs':
        input("note zfs boot/root is not working, many fixes will be needed, press enter to break things")

    safety_check_devices(boot_device=boot_device,
                         root_devices=root_devices,
                         verbose=verbose,
                         debug=debug,
                         boot_device_partition_table=boot_device_partition_table,
                         boot_filesystem=boot_filesystem,
                         root_device_partition_table=root_device_partition_table,
                         root_filesystem=root_filesystem,
                         force=force,)

    if boot_device and root_devices and not vm:
        if boot_device == root_devices[0]:
            assert boot_filesystem == root_filesystem
            assert boot_device_partition_table == root_device_partition_table
            if boot_filesystem == 'zfs':
                ctx.invoke(destroy_block_devices_head_and_tail,
                           devices=root_devices,
                           force=True,
                           no_backup=True,
                           size=(1024 * 1024 * 128),
                           note=False,
                           verbose=verbose,
                           debug=debug,)
                # if this is zfs, it will make a gpt table, / and EFI partition
                ctx.invoke(create_root_device,
                           devices=root_devices,
                           exclusive=True,
                           filesystem=root_filesystem,
                           partition_table=root_device_partition_table,
                           force=True,
                           raid=raid,
                           raid_group_size=raid_group_size,
                           pool_name=hostname,)
                create_boot_device(ctx,
                                   device=boot_device,
                                   partition_table='none',
                                   filesystem=boot_filesystem,
                                   force=True,
                                   verbose=verbose,
                                   debug=debug,)  # dont want to delete the gpt that zfs made
                boot_mount_command = False
                root_mount_command = False

            elif boot_filesystem == 'ext4':
                ctx.invoke(destroy_block_device_head_and_tail,
                           device=boot_device,
                           force=True,)
                create_boot_device(ctx,
                                   device=boot_device,
                                   partition_table=boot_device_partition_table,
                                   filesystem=boot_filesystem,
                                   force=True,
                                   verbose=verbose,
                                   debug=debug,)  # writes gurb_bios from 48s to 1023s then writes EFI partition from 1024s to 205824s (100M efi) (nope, too big for fat16)
                ctx.invoke(create_root_device,
                           devices=root_devices,
                           exclusive=False,
                           filesystem=root_filesystem,
                           partition_table=root_device_partition_table,
                           force=True,
                           raid=raid,
                           raid_group_size=raid_group_size,
                           pool_name=hostname,)
                root_partition_path = add_partition_number_to_device(device=root_devices[0], partition_number="3")
                root_mount_command = "mount " + root_partition_path.as_posix() + " " + str(mount_path)
                boot_mount_command = False
            else:  # unknown case
                assert False
        else:
            eprint("differing root and boot devices: (exclusive) root_devices[0]:", root_devices[0], "boot_device:", boot_device)
            create_boot_device(ctx,
                               device=boot_device,
                               partition_table=boot_device_partition_table,
                               filesystem=boot_filesystem,
                               force=True,
                               verbose=verbose,
                               debug=debug,)
            ctx.invoke(write_boot_partition,
                       device=boot_device,
                       force=True,
                       verbose=verbose,
                       debug=debug,)
            ctx.invoke(create_root_device,
                       devices=root_devices,
                       exclusive=True,
                       filesystem=root_filesystem,
                       partition_table=root_device_partition_table,
                       force=True,
                       raid=raid,)
            if root_filesystem == 'zfs':
                assert False
                root_mount_command = False
            elif root_filesystem == 'ext4':
                root_partition_path = add_partition_number_to_device(device=root_devices[0], partition_number="1")
                root_mount_command = "mount " + root_partition_path.as_posix() + " " + mount_path.as_posix()

            boot_partition_path = add_partition_number_to_device(device=boot_device, partition_number="3")
            boot_mount_command = "mount " + boot_partition_path.as_posix() + " " + mount_path_boot.as_posix()

        if root_mount_command:
            run_command(root_mount_command)

        assert path_is_mounted(mount_path, verbose=verbose, debug=debug,)

        os.makedirs(mount_path_boot, exist_ok=True)

        if boot_mount_command:
            run_command(boot_mount_command)
            assert path_is_mounted(mount_path_boot, verbose=verbose, debug=debug,)
        else:
            assert not path_is_mounted(mount_path_boot, verbose=verbose, debug=debug,)

        if boot_device:
            os.makedirs(mount_path_boot_efi, exist_ok=True)

        if boot_filesystem == 'zfs':
            efi_partition_path = add_partition_number_to_device(device=boot_device, partition_number="9")
            efi_mount_command = "mount " + efi_partition_path.as_posix() + " " + mount_path_boot_efi.as_posix()
        else:
            efi_partition_path = add_partition_number_to_device(device=boot_device, partition_number="2")
            efi_mount_command = "mount " + efi_partition_path.as_posix() + " " + mount_path_boot_efi.as_posix()

        if boot_device:
            run_command(efi_mount_command)
            assert path_is_mounted(mount_path_boot_efi, verbose=verbose, debug=debug,)

    install_stage3(stdlib=stdlib,
                   multilib=multilib,
                   distfiles_dir=distfiles_dir,
                   arch=arch,
                   destination=mount_path,
                   vm=vm,
                   vm_ram=vm_ram,
                   verbose=verbose,
                   debug=debug,)

    if not boot_device:
        assert False
        #boot_device = "False"  # fixme

    ctx.invoke(chroot_gentoo,
               mount_path=mount_path,
               stdlib=stdlib,
               boot_device=boot_device,
               hostname=hostname,
               march=march,
               root_filesystem=root_filesystem,
               newpasswd=newpasswd,
               ip=ip,
               ip_gateway=ip_gateway,
               vm=vm,
               ipython=False,
               skip_to_rsync=False,
               verbose=verbose,
               debug=debug,)

