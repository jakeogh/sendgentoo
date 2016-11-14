#!/usr/bin/env python3

import requests
import click
import sys
from gentoo_setup_get_stage3_url import get_stage3_url
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
    return local_filename

def download_stage3(c_std_lib, url=False):
    if not url:
        url = get_stage3_url(c_std_lib)
    #cprint(url)
    stage3_file = download_file(url)
    download_file(url+'.CONTENTS')
    download_file(url+'.DIGESTS')
    download_file(url+'.DIGESTS.asc')
    return stage3_file

@click.command()
@click.option('--c-std-lib', is_flag=False, required=True, type=click.Choice(['glibc', 'musl', 'uclibc']), help=HELP)
def main(c_std_lib):
    download_stage3(c_std_lib)
    #url = get_stage3_url(c_std_lib)
    #cprint(url)
    #download_file(url)

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

