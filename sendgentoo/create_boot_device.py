#!/usr/bin/env python3

import click
from kcl.fileops import path_is_block_special
from kcl.mountops import block_special_path_is_mounted
from kcl.printops import eprint
from kcl.deviceops import write_gpt
from kcl.deviceops import write_grub_bios_partition
from kcl.deviceops import write_efi_partition
from kcl.deviceops import create_filesystem
from kcl.deviceops import warn

def create_boot_device(ctx, device, partition_table, filesystem, force):
    assert not device[-1].isdigit()
    eprint("installing gpt/grub_bios/efi on boot device:", device, '(' + partition_table + ')', '(' + filesystem + ')')
    assert path_is_block_special(device)
    assert not block_special_path_is_mounted(device)

    if not force:
        warn((device,))

    # dont do this here, want to be able to let zfs make the gpt and it's partitions before making bios_grub and EFI
    #destroy_block_device_head_and_tail(device=device, force=True)

    if partition_table == 'gpt':
        if filesystem != 'zfs':
            ctx.invoke(write_gpt, device=device, no_wipe=True, force=force, no_backup=False) # zfs does this

    if filesystem == 'zfs':
        ctx.invoke(write_grub_bios_partition, device=device, force=True, start='48s', end='1023s', partition_number='2') #2 if zfs made sda1 and sda9
    else:
        ctx.invoke(write_grub_bios_partition, device=device, force=True, start='48s', end='1023s', partition_number='1')

    if filesystem != 'zfs':
        ctx.invoke(write_efi_partition, device=device, force=True, start='1024s', end='18047s', partition_number='2') # this is /dev/sda9 on zfs

    if filesystem == 'zfs':
        create_filesystem(device=device + '9', partition_type='fat16', force=True)

@click.command()
@click.option('--device',          is_flag=False, required=True)
@click.option('--partition-table', is_flag=False, required=True, type=click.Choice(['gpt']))
@click.option('--filesystem',      is_flag=False, required=True, type=click.Choice(['ext4', 'zfs']))
@click.option('--force',           is_flag=True,  required=False)
@click.pass_context
def main(ctx, device, partition_table, filesystem, force):
    create_boot_device(ctx, device=device, partition_table=partition_table, filesystem=filesystem, force=force)


if __name__ == '__main__':
    main()
