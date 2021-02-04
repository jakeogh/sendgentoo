#!/usr/bin/env python3

# pylint: disable=C0111     # docstrings are always outdated and wrong
# pylint: disable=W0511     # todo is encouraged
# pylint: disable=R0902     # too many instance attributes
# pylint: disable=C0302     # too many lines in module
# pylint: disable=C0103     # single letter var names
# pylint: disable=R0911     # too many return statements
# pylint: disable=R0912     # too many branches
# pylint: disable=R0915     # too many statements
# pylint: disable=R0913     # too many arguments
# pylint: disable=R1702     # too many nested blocks
# pylint: disable=R0914     # too many local variables
# pylint: disable=R0903     # too few public methods
# pylint: disable=E1101     # no member for base
# pylint: disable=W0201     # attribute defined outside __init__


import os
import sys
#import time
from pathlib import Path

import click
import humanfriendly
from compile_kernel.compile_kernel import kcompile
from icecream import ic
from kcl.commandops import run_command
from kcl.deviceops import add_partition_number_to_device
from kcl.deviceops import create_filesystem
from kcl.deviceops import destroy_block_device
from kcl.deviceops import destroy_block_device_head_and_tail
from kcl.deviceops import destroy_block_devices_head_and_tail
from kcl.deviceops import luksformat
from kcl.fileops import get_block_device_size
from kcl.mountops import block_special_path_is_mounted
from kcl.mountops import path_is_mounted
from kcl.pathops import path_is_block_special
from kcl.printops import eprint
from kcl.userops import root_user
from kcl.warnops import warn
from psutil import virtual_memory

from sendgentoo.create_boot_device import create_boot_device
from sendgentoo.create_root_device import create_root_device
from sendgentoo.create_zfs_filesystem import create_zfs_filesystem
from sendgentoo.create_zfs_pool import create_zfs_pool
from sendgentoo.install_stage3 import install_stage3
from sendgentoo.write_boot_partition import write_boot_partition


def validate_ram_size(ctx, param, vm_ram):
    eprint("vm_ram:", vm_ram)

    sysram_bytes = virtual_memory().total
    vm_ram_bytes = humanfriendly.parse_size(vm_ram)
    if vm_ram_bytes >= sysram_bytes:
        sysram_human = humanfriendly.format_size(sysram_bytes)
        vm_ram_human = humanfriendly.format_size(vm_ram_bytes)
        raise click.BadParameter('You entered {0} for --vm-ram but the host system only has {1}. Exiting.'.format(vm_ram_human, sysram_human))
    return vm_ram_bytes


@click.group()
@click.pass_context
def sendgentoo(ctx):
    pass


sendgentoo.add_command(destroy_block_device)
sendgentoo.add_command(destroy_block_device_head_and_tail)
sendgentoo.add_command(luksformat)
sendgentoo.add_command(create_filesystem)
sendgentoo.add_command(create_zfs_pool)
sendgentoo.add_command(create_zfs_filesystem)
sendgentoo.add_command(create_root_device)
#sendgentoo.add_command(create_boot_device)

@sendgentoo.command()
@click.option('--boot-device',                 is_flag=False, required=True)
@click.option('--force',                       is_flag=True,  required=False)
@click.option('--no-configure-kernel',         is_flag=True,  required=False)
@click.option('--verbose',                     is_flag=True,  required=False)
@click.option('--debug',                       is_flag=True,  required=False)
@click.pass_context
def compile_kernel(ctx,
                   boot_device,
                   no_configure_kernel: bool,
                   force: bool,
                   verbose: bool,
                   debug: bool,):

    if not root_user():
        ic('You must be root.')
        sys.exit(1)

    configure_kernel = not no_configure_kernel

    mount_path_boot = Path('/boot')
    ic(mount_path_boot)
    assert not path_is_mounted(mount_path_boot)

    mount_path_boot_efi = mount_path_boot / Path('efi')
    ic(mount_path_boot_efi)
    assert not path_is_mounted(mount_path_boot_efi)

    if not Path(boot_device).name.startswith('nvme'):
        assert not boot_device[-1].isdigit()
    #ic('installing grub on boot device:',
    #   boot_device,
    #   boot_device_partition_table,
    #   boot_filesystem)

    assert path_is_block_special(boot_device)
    assert not block_special_path_is_mounted(boot_device)
    warn((boot_device,), msg="about to update the kernel on device:")
    #if not force:
    #    warn((boot_device,))
    #create_boot_device(ctx,
    #                   device=boot_device,
    #                   partition_table=boot_device_partition_table,
    #                   filesystem=boot_filesystem,
    #                   force=True,
    #                   verbose=verbose,
    #                   debug=debug,)
    #ctx.invoke(write_boot_partition,
    #           device=boot_device,
    #           force=True,
    #           verbose=verbose,
    #           debug=debug,)

    #hybrid_mbr_command = "/home/cfg/_myapps/sendgentoo/sendgentoo/gpart_make_hybrid_mbr.sh" + " " + boot_device
    #run_command(hybrid_mbr_command, verbose=True, popen=True)

    os.makedirs(mount_path_boot, exist_ok=True)
    boot_partition_path = add_partition_number_to_device(device=boot_device, partition_number="3")
    boot_mount_command = "mount " + boot_partition_path + " " + str(mount_path_boot)
    assert not path_is_mounted(mount_path_boot)
    run_command(boot_mount_command, verbose=True, popen=True)
    assert path_is_mounted(mount_path_boot)

    os.makedirs(mount_path_boot_efi, exist_ok=True)

    efi_partition_path = add_partition_number_to_device(device=boot_device, partition_number="2")
    efi_mount_command = "mount " + efi_partition_path + " " + str(mount_path_boot_efi)
    assert not path_is_mounted(mount_path_boot_efi)
    run_command(efi_mount_command, verbose=True, popen=True)
    assert path_is_mounted(mount_path_boot_efi)

    #grub_install_command = "/home/cfg/_myapps/sendgentoo/sendgentoo/post_chroot_install_grub.sh" + " " + boot_device
    #run_command(grub_install_command, verbose=True, popen=True)

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
@click.option('--compile-kernel', "_compile_kernel", is_flag=True,  required=False)
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
    assert not path_is_mounted(mount_path_boot)

    mount_path_boot_efi = mount_path_boot / Path('efi')
    ic(mount_path_boot_efi)
    assert not path_is_mounted(mount_path_boot_efi)

    if not Path(boot_device).name.startswith('nvme'):
        assert not boot_device[-1].isdigit()
    ic('installing grub on boot device:',
       boot_device,
       boot_device_partition_table,
       boot_filesystem)
    assert path_is_block_special(boot_device)
    assert not block_special_path_is_mounted(boot_device)
    if not force:
        warn((boot_device,))
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
    assert not path_is_mounted(mount_path_boot)
    run_command(boot_mount_command, verbose=True, popen=True)
    assert path_is_mounted(mount_path_boot)

    os.makedirs(mount_path_boot_efi, exist_ok=True)

    efi_partition_path = add_partition_number_to_device(device=boot_device, partition_number="2")
    efi_mount_command = "mount " + efi_partition_path + " " + str(mount_path_boot_efi)
    assert not path_is_mounted(mount_path_boot_efi)
    run_command(efi_mount_command, verbose=True, popen=True)
    assert path_is_mounted(mount_path_boot_efi)

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


@sendgentoo.command()
@click.argument('root_devices',                required=False, nargs=-1)  # --vm does not need a specified root device
@click.option('--vm',                          is_flag=False, required=False, type=click.Choice(['qemu']))
@click.option('--vm-ram',                      is_flag=False, required=False, type=str, callback=validate_ram_size, default=str(1024**3))
@click.option('--boot-device',                 is_flag=False, required=True)
@click.option('--boot-device-partition-table', is_flag=False, required=False, type=click.Choice(['gpt']), default="gpt")
@click.option('--root-device-partition-table', is_flag=False, required=False, type=click.Choice(['gpt']), default="gpt")
@click.option('--boot-filesystem',             is_flag=False, required=False, type=click.Choice(['ext4', 'zfs']), default="ext4")
@click.option('--root-filesystem',             is_flag=False, required=True,  type=click.Choice(['ext4', 'zfs', '9p']), default="ext4")
@click.option('--c-std-lib',                   is_flag=False, required=False, type=click.Choice(['glibc', 'musl', 'uclibc']), default="glibc")
@click.option('--arch',                        is_flag=False, required=False, type=click.Choice(['alpha', 'amd64', 'arm', 'hppa', 'ia64', 'mips', 'ppc', 's390', 'sh', 'sparc', 'x86']), default="amd64")
@click.option('--raid',                        is_flag=False, required=False, type=click.Choice(['disk', 'mirror', 'raidz1', 'raidz2', 'raidz3', 'raidz10', 'raidz50', 'raidz60']), default="disk")
@click.option('--raid-group-size',             is_flag=False, required=False, type=click.IntRange(1, 2), default=1)
@click.option('--march',                       is_flag=False, required=True, type=click.Choice(['native', 'nocona']))
#@click.option('--pool-name',                   is_flag=False, required=True, type=str)
@click.option('--hostname',                    is_flag=False, required=True)
@click.option('--newpasswd',                   is_flag=False, required=True)
@click.option('--ip',                          is_flag=False, required=True)
@click.option('--ip-gateway',                  is_flag=False, required=True)
@click.option('--force',                       is_flag=True,  required=False)
@click.option('--encrypt',                     is_flag=True,  required=False)
@click.option('--multilib',                    is_flag=True,  required=False)
@click.option('--minimal',                     is_flag=True,  required=False)
@click.option('--verbose',                     is_flag=True,  required=False)
@click.option('--debug',                       is_flag=True,  required=False)
@click.pass_context
def install(ctx, *,
            root_devices: tuple,
            vm: str,
            vm_ram: str,
            boot_device: str,
            boot_device_partition_table: str,
            root_device_partition_table: str,
            boot_filesystem: str,
            root_filesystem: str,
            c_std_lib: str,
            arch: str,
            raid: str,
            raid_group_size: int,
            march: str,
            hostname: str,
            newpasswd: str,
            ip: str,
            ip_gateway: str,
            force: bool,
            encrypt: bool,
            multilib: bool,
            minimal: bool,
            verbose: bool,
            debug: bool,):
    assert isinstance(root_devices, tuple)
    assert hostname.lower() == hostname
    os.makedirs('/usr/portage/distfiles', exist_ok=True)

    #if not os.path.isdir('/usr/portage/sys-kernel'):
    #    eprint("run emerge --sync first")
    #    quit(1)
    if encrypt:
        eprint("encryption not yet supported")
        #quit(1)
    if c_std_lib == 'musl':
        eprint("musl not supported yet")
        quit(1)
    if c_std_lib == 'uclibc':
        eprint("uclibc fails with efi grub because efivar fails to compile. See Note.")
        quit(1)

    mount_path = Path("/mnt/gentoo")
    mount_path_boot = mount_path / Path('boot')
    mount_path_boot_efi = mount_path_boot / Path('efi')

    assert Path('/sbin/ischroot').exists()

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

    if boot_device:
        if not Path(boot_device).name.startswith('nvme'):
            assert not boot_device[-1].isdigit()

    for device in root_devices:
        if not Path(device).name.startswith('nvme'):
            assert not device[-1].isdigit()

    #if raid:
    #    assert root_filesystem == 'zfs'

    if boot_device:
        eprint("installing gentoo on boot device:", boot_device, '(' + boot_device_partition_table + ')', '(' + boot_filesystem + ')')
        assert path_is_block_special(boot_device)
        assert not block_special_path_is_mounted(boot_device)

    if root_devices:
        eprint("installing gentoo on root device(s):", root_devices, '(' + root_device_partition_table + ')', '(' + root_filesystem + ')')
        for device in root_devices:
            assert path_is_block_special(device)
            assert not block_special_path_is_mounted(device)

    eprint("using C library:", c_std_lib)
    eprint("hostname:", hostname)

    for device in root_devices:
        eprint("boot_device:", boot_device)
        eprint("device:", device)
        eprint("get_block_device_size(boot_device):", get_block_device_size(boot_device))
        eprint("get_block_device_size(device):     ", get_block_device_size(device))
        assert get_block_device_size(boot_device) <= get_block_device_size(device)

    if root_devices:
        first_root_device_size = get_block_device_size(root_devices[0])

        for device in root_devices:
            assert get_block_device_size(device) == first_root_device_size

    if boot_device or root_devices:
        if not force:
            warn((boot_device,))
            warn(root_devices)

    os.makedirs(mount_path, exist_ok=True)

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
                                   debug=debug,) # dont want to delete the gpt that zfs made
                boot_mount_command = False
                root_mount_command = False

            elif boot_filesystem == 'ext4':
                ctx.invoke(destroy_block_device_head_and_tail,
                           device=device,
                           force=True,)
                create_boot_device(ctx,
                                   device=boot_device,
                                   partition_table=boot_device_partition_table,
                                   filesystem=boot_filesystem,
                                   force=True,
                                   verbose=verbose,
                                   debug=debug,) # writes gurb_bios from 48s to 1023s then writes EFI partition from 1024s to 205824s (100M efi) (nope, too big for fat16)
                ctx.invoke(create_root_device,
                           devices=root_devices,
                           exclusive=False,
                           filesystem=root_filesystem,
                           partition_table=root_device_partition_table,
                           force=True,
                           raid=raid,
                           raid_group_size=raid_group_size,
                           pool_name=hostname,)
                root_partition_path = add_partition_number_to_device(device=device, partition_number="3")
                root_mount_command = "mount " + root_partition_path + " " + str(mount_path)
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
                root_mount_command = False
            elif root_filesystem == 'ext4':
                root_partition_path = add_partition_number_to_device(device=device, partition_number="1")
                root_mount_command = "mount " + root_partition_path + " " + str(mount_path)

            boot_partition_path = add_partition_number_to_device(device=boot_device, partition_number="3")
            boot_mount_command = "mount " + boot_partition_path + " " + str(mount_path_boot)

        if root_mount_command:
            run_command(root_mount_command)

        assert path_is_mounted(mount_path)

        os.makedirs(mount_path_boot, exist_ok=True)

        if boot_mount_command:
            run_command(boot_mount_command)
            assert path_is_mounted(mount_path_boot)
        else:
            assert not path_is_mounted(mount_path_boot)

        if boot_device:
            os.makedirs(mount_path_boot_efi, exist_ok=True)

        if boot_filesystem == 'zfs':
            efi_partition_path = add_partition_number_to_device(device=boot_device, partition_number="9")
            efi_mount_command = "mount " + efi_partition_path + " " + str(mount_path_boot_efi)
        else:
            efi_partition_path = add_partition_number_to_device(device=boot_device, partition_number="2")
            efi_mount_command = "mount " + efi_partition_path + " " + str(mount_path_boot_efi)

        if boot_device:
            run_command(efi_mount_command)
            assert path_is_mounted(mount_path_boot_efi)

    install_stage3(c_std_lib=c_std_lib,
                   multilib=multilib,
                   arch=arch,
                   destination=mount_path,
                   vm=vm,
                   vm_ram=vm_ram,)

    #if march == 'native':
    if not boot_device:
        boot_device = "False"  # fixme
    if not vm:
        vm = "novm"
    chroot_gentoo_command = \
        "/home/cfg/_myapps/sendgentoo/sendgentoo/chroot_gentoo.sh " + \
        c_std_lib + " " + \
        boot_device + " " + \
        hostname + ' ' + \
        march + ' ' + \
        root_filesystem + ' ' + \
        newpasswd + ' ' + \
        ip + ' ' + \
        ip_gateway + ' ' + \
        vm + ' ' + \
        str(mount_path)
    eprint("\nnow run:", chroot_gentoo_command)
    return
