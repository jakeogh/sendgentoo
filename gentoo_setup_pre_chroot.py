#!/usr/bin/env python3

import os
import click
import time
import subprocess
from kcl.fileops import path_is_block_special
from kcl.fileops import block_special_path_is_mounted
#from make_one_primary_partition import BlockDevice
from kcl.command import run_command
from gentoo_setup_install_stage3 import install_stage3
from destroy_block_device_head_and_tail import destroy_block_device_head_and_tail

def get_file_size(filename):
    fd = os.open(filename, os.O_RDONLY)
    try:
        return os.lseek(fd, 0, os.SEEK_END)
    finally:
        os.close(fd)

#def destroy_block_device_header(device):
#    assert path_is_block_special(device)
#    assert not block_special_path_is_mounted(device)
#    with open(device, 'wb') as dh:
#        #dh.write(bytearray(1024))
#        dh.write(bytearray(1024*1024*256))
#    return True
#
#def destroy_block_device_end(device):
#    device_size = get_file_size(device)
#    print("device_size:", device_size)
#    location_to_start = device_size - (1024*1024*128)
#    print("location_to_start:", location_to_start)
#    with open(device, 'wb') as dh:
#        dh.seek(location_to_start)
#        dh.write(bytearray(1024*1024*128))
#    return True


HELP = "temp"
@click.command()
@click.option('--encrypt',         is_flag=True,  required=False, help=HELP)
@click.option('--boot-device',     is_flag=False, required=True, help=HELP)
@click.option('--root-device',     is_flag=False, required=True, help=HELP)
@click.option('--boot-device-partition-table', is_flag=False, required=True, type=click.Choice(['gpt']), help=HELP)
@click.option('--root-device-partition-table', is_flag=False, required=True, type=click.Choice(['gpt']), help=HELP)
@click.option('--boot-device-filesystem', is_flag=False, required=True, type=click.Choice(['ext4']),     help=HELP)
@click.option('--root-device-filesystem', is_flag=False, required=True, type=click.Choice(['ext4']),     help=HELP)
@click.option('--c-std-lib',              is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']), help=HELP)
@click.option('--hostname',               is_flag=False, required=True,  help=HELP)
@click.option('--force',                  is_flag=True,  required=False, help=HELP)
def install_gentoo(encrypt, boot_device, root_device, boot_device_partition_table, root_device_partition_table, boot_device_filesystem, root_device_filesystem, c_std_lib, hostname, force):
    if encrypt:
        print("encryption not yet supported")
        quit(1)

    if c_std_lib == 'musl':
        print("musl not supported yet")
        quit(1)

    if c_std_lib == 'uclibc':
        print("uclibc fails with efi grub because efivar fails to compile. See Note.")
        quit(1)

    assert not boot_device[-1].isdigit()
    assert not root_device[-1].isdigit()

    print("installing gentoo on boot device:", boot_device, '(' + boot_device_partition_table + ')', '(' + boot_device_filesystem + ')')
    assert path_is_block_special(boot_device)
    umount_command = "/home/cfg/setup/gentoo_installer/umount_mnt_gentoo.sh"
    run_command(umount_command)
    assert not block_special_path_is_mounted(boot_device)

    print("installing gentoo on root device:", root_device, '(' + root_device_partition_table + ')', '(' + root_device_filesystem + ')')
    assert path_is_block_special(root_device)
    assert not block_special_path_is_mounted(root_device)

    assert os.getcwd() == '/home/cfg/setup/gentoo_installer'
    print("using C standard library:", c_std_lib)
    print("hostname:", hostname)

    if not force:
        print("THIS WILL DESTROY ALL DATA ON THIS COMPUTER, _REMOVE_ ANY HARD DRIVES (and removable storage like USB sticks) WHICH YOU DO NOT WANT TO DELETE THE DATA ON")
        answer = input("Do you want to proceed with deleting all of your data? (you must type YES to proceed)")
        if answer != 'YES':
            quit(1)
        print("Sleeping 5 seconds")
        time.sleep(1)

    if boot_device == root_device:
        assert boot_device_filesystem      == root_device_filesystem
        assert boot_device_partition_table == root_device_partition_table

        destroy_block_device_head_and_tail(device=boot_device, force=True)
        #run_command("sgdisk --zap-all " + boot_device)

        run_command("parted " + boot_device + " --script -- mklabel gpt")
        #run_command("sgdisk --clear " + boot_device) #alt way to greate gpt label

        run_command("parted " + boot_device + " --script -- mkpart primary 1MiB 3MiB")
        run_command("parted " + boot_device + " --script -- name 1 BIOS")
        run_command("parted " + boot_device + " --script -- set 1 bios_grub on")

        run_command("parted " + boot_device + " --script -- mkpart primary 3MiB 100MiB")
        run_command("parted " + boot_device + " --script -- name 2 EFI")
        run_command("parted " + boot_device + " --script -- set 2 boot on")
        run_command("mkfs.fat -F32 " + boot_device + "2")

        #boot_partition_command = "parted " + boot_device + " --script -- mkpart primary 200MiB 331MiB"
        #run_command(boot_partition_command)
        #set_boot_name_command = "parted " + boot_device + " --script -- name 2 grub"
        #run_command(set_boot_name_command)
        #command = "mkfs.ext4 " + boot_device + "2"
        #run_command(command)

        run_command("parted " + boot_device + " --script -- mkpart primary 100MiB 100%")
        run_command("parted " + boot_device + " --script -- name 3 rootfs")
        run_command("mkfs.ext4 " + boot_device + "3")

        #set_boot_on_command = "parted " + boot_device + " --script -- set 2 boot on"
        #run_command(set_boot_on_command)
        #root_partition_boot_flag_command = "parted " + boot_device + " --script -- set 2 boot on"
        #run_command(root_partition_boot_flag_command)

        try:
            os.mkdir('/mnt/gentoo')
        except FileExistsError:
            pass

        root_mount_command = "mount " + boot_device + "3 /mnt/gentoo"
        run_command(root_mount_command)

        try:
            os.mkdir('/mnt/gentoo/boot')
        except FileExistsError:
            pass

        try:
            os.mkdir('/mnt/gentoo/boot/efi')
        except FileExistsError:
            pass

        run_command("mount " + boot_device + "2 /mnt/gentoo/boot/efi")
        install_stage3(c_std_lib)
        #run_command("/home/cfg/setup/gentoo_installer/download_and_install_stage3.sh")

        #output = run_command("/home/cfg/setup/gentoo_installer/configure_etc.sh " + hostname)
        #print("configure_etc.sh output:", output)

        chroot_gentoo_command = "/home/cfg/setup/gentoo_installer/chroot_gentoo.sh " + c_std_lib + " " + boot_device + " " + hostname
        print("now run:", chroot_gentoo_command)

        return

    else:
        print("differing root and boot devices, not supported yet")
        quit(1)

if __name__ == '__main__':
    install_gentoo()
    quit(0)

