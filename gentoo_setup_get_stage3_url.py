#!/usr/bin/env python3
import requests
import click
import sys
from kcl.printops import cprint

HELP="temp"

def download_file(url):
    local_filename = '/usr/portage/distfiles/' + url.split('/')[-1]
    r = requests.get(url, stream=True)
    try:
        with open(local_filename, 'bx') as fh:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    fh.write(chunk)
    except FileExistsError:
        cprint("skipping download, file exists:", local_filename)
    r.close()

def get_stage3_url(c_std_lib):
    mirror = 'http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/'
    if c_std_lib == 'glibc':
        latest = 'latest-stage3-amd64-hardened+nomultilib.txt'
    if c_std_lib == 'musl':
        latest = ''
        cprint("cant use musl yet")
        quit(1)
    if c_std_lib == 'uclibc':
        latest = 'latest-stage3-amd64-uclibc-hardened.txt'
        cprint("uclibc wont compile efivars")
        quit(1)
    r = requests.get(mirror + latest)
    autobuild_file_lines = r.text.split('\n')
    r.close()
    for line in autobuild_file_lines:
        if 'stage3-amd64' in line:
            path = line.split(' ')[0]
            break
    #cprint('path:', path)
    url = mirror + path
    #cprint("url:", url)
    return url


@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']), help=HELP)
def main(c_std_lib):
    url = get_stage3_url(c_std_lib)
    cprint(url)
    download_file(url)


if __name__ == '__main__':
    main()
    #cprint("url:", url)


#cd /mnt/gentoo || exit 1
#stage_path=`curl -s http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/latest-stage3-amd64-hardened+nomultilib.txt | tail -n 1 | cut -d ' ' -f 1`
#stage_file=`curl -s http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/latest-stage3-amd64-hardened+nomultilib.txt | tail -n 1 | cut -d '/' -f 3 | cut -d ' ' -f 1`
#
#echo "stage_file: ${stage_file}"
#
#wget "http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/${stage_path}" || exit 1
#wget "http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/${stage_path}.CONTENTS" || exit 1
#wget "http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/${stage_path}.DIGESTS" || exit 1
#wget "http://ftp.ucsb.edu/pub/mirrors/linux/gentoo/releases/amd64/autobuilds/${stage_path}.DIGESTS.asc" || exit 1
#gpg --keyserver keyserver.ubuntu.com --recv-key 0x2D182910
#gpg --verify "${stage_file}.DIGESTS.asc"
#tar xjpf stage3-*.tar.bz2 || exit 1


#cd /mnt/gentoo || exit 1
#file_name=`curl -s http://distfiles.gentoo.org/experimental/amd64/musl/ 2>&1 | grep -o -E 'href="([^"#]+)"' | cut -d'"' -f2 | grep "hardened-*.*.bz2$"`
#stage_file="http://distfiles.gentoo.org/experimental/amd64/musl/${file_name}"
#echo "stage_file: ${stage_file}"
#
#wget "${stage_file}"
#wget "${stage_file}.CONTENTS"
#wget "${stage_file}.DIGESTS"
#echo "decompressing stage3..."
#tar xjpf stage3-*.tar.bz2 || exit 1


