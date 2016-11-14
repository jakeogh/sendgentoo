#!/usr/bin/env python3

import os
import sys
import click
import time
import subprocess
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
from kcl.fileops import path_is_mounted
from kcl.command import run_command
from gentoo_setup_install_stage3 import install_stage3
from destroy_block_device_head_and_tail import destroy_block_device_head_and_tail
#from write_gpt import write_gpt
#from write_sysfs_partition import write_sysfs_partition
from create_boot_device import create_boot_device
from create_root_device import create_root_device
from kcl.printops import cprint
from write_boot_partition import write_boot_partition

def get_file_size(filename):
    fd = os.open(filename, os.O_RDONLY)
    try:
        return os.lseek(fd, 0, os.SEEK_END)
    finally:
        os.close(fd)

@click.command()
@click.option('--boot-device',                 is_flag=False, required=True)
@click.option('--root-device',                 is_flag=False, required=True)
@click.option('--boot-device-partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
@click.option('--root-device-partition-table', is_flag=False, required=True, type=click.Choice(['gpt', 'zfs']))
@click.option('--boot-filesystem',             is_flag=False, required=True, type=click.Choice(['ext4']))
@click.option('--root-filesystem',             is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
@click.option('--c-std-lib',                   is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']))
@click.option('--march',                       is_flag=False, required=True, type=click.Choice(['native', 'nocona']))
@click.option('--hostname',                    is_flag=False, required=True)
@click.option('--force',                       is_flag=True,  required=False)
@click.option('--encrypt',                     is_flag=True,  required=False)
def install_gentoo(boot_device, root_device, boot_device_partition_table, root_device_partition_table, boot_filesystem, root_filesystem, c_std_lib, march, hostname, force, encrypt):
    if encrypt:
        cprint("encryption not yet supported")
        quit(1)
    if c_std_lib == 'musl':
        cprint("musl not supported yet")
        quit(1)
    if c_std_lib == 'uclibc':
        cprint("uclibc fails with efi grub because efivar fails to compile. See Note.")
        quit(1)

    assert not boot_device[-1].isdigit()
    assert not root_device[-1].isdigit()
    cprint("installing gentoo on boot device:", boot_device, '(' + boot_device_partition_table + ')', '(' + boot_filesystem + ')')
    assert path_is_block_special(boot_device)
    #umount_command = "/home/cfg/setup/gentoo_installer/umount_mnt_gentoo.sh"
    #run_command(umount_command)
    assert not block_special_path_is_mounted(boot_device)
    cprint("installing gentoo on root device:", root_device, '(' + root_device_partition_table + ')', '(' + root_filesystem + ')')
    assert path_is_block_special(root_device)
    assert not block_special_path_is_mounted(root_device)
    assert os.getcwd() == '/home/cfg/setup/gentoo_installer'
    cprint("using C standard library:", c_std_lib)
    cprint("hostname:", hostname)

    if not force:
        cprint("THIS WILL DESTROY ALL DATA ON THIS COMPUTER, _REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        cprint("Sleeping 5 seconds")
        time.sleep(1)

    try:
        os.mkdir('/mnt/gentoo')
    except FileExistsError:
        pass

    if boot_device == root_device:
        assert root_filesystem != 'zfs' # cant do zfs root on a single disk
        assert boot_filesystem  == root_filesystem
        assert boot_device_partition_table == root_device_partition_table
        create_boot_device(device=boot_device, partition_table=boot_device_partition_table, filesystem=boot_filesystem, force=True)
        create_root_device(device=root_device, exclusive=False, filesystem=root_filesystem, partition_table=root_device_partition_table, force=True)
        root_mount_command = "mount " + root_device + "3 /mnt/gentoo"
        boot_mount_command = False

    else:
        cprint("differing root and boot devices: (exclusive) root_device:", root_device, "boot_device:", boot_device)
        create_boot_device(device=boot_device, partition_table=boot_device_partition_table, filesystem=boot_filesystem, force=True)
        write_boot_partition(device=boot_device, force=True)
        create_root_device(device=root_device, exclusive=True, filesystem=root_filesystem, partition_table=root_device_partition_table, force=True)
        root_mount_command = "mount " + root_device + "1 /mnt/gentoo"
        boot_mount_command = "mount " + boot_device + "3 /mnt/gentoo/boot"

    run_command(root_mount_command)
    #from IPython import embed; embed()

    assert path_is_mounted('/mnt/gentoo')

    try:
        os.mkdir('/mnt/gentoo/boot')
    except FileExistsError:
        pass

    if boot_mount_command:
        run_command(boot_mount_command)
        assert path_is_mounted('/mnt/gentoo/boot')
    else:
        assert not path_is_mounted('/mnt/gentoo/boot')

    try:
        os.mkdir('/mnt/gentoo/boot/efi')
    except FileExistsError:
        pass

    run_command("mount " + boot_device + "2 /mnt/gentoo/boot/efi")
    install_stage3(c_std_lib)

    if march == 'native':
        chroot_gentoo_command = "/home/cfg/setup/gentoo_installer/chroot_gentoo.sh " + c_std_lib + " " + boot_device + " " + hostname + ' native'
    elif march == 'nocona':
        chroot_gentoo_command = "/home/cfg/setup/gentoo_installer/chroot_gentoo.sh " + c_std_lib + " " + boot_device + " " + hostname + ' nocona'
    cprint("now run:", chroot_gentoo_command)
    return

if __name__ == '__main__':
    install_gentoo()
    quit(0)

