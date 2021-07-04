#!/usr/bin/env python3

# flake8: noqa           # flake8 has no per file settings :(
# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=C0114  #      Missing module docstring (missing-module-docstring)
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


from pathlib import Path

import sh
from asserttool import eprint
from asserttool import ic
from pathtool import write_line_to_file


def emerge_world(*,
                 verbose: bool,
                 debug: bool,
                 ):
    ic()
    sh.emerge('-p', '-v',       '--backtrack=130', '--usepkg=n', '--tree', '-u', '--ask', 'n', '-n', '@world')
    sh.emerge('-p', '-v', '-F', '--backtrack=130', '--usepkg=n', '--tree', '-u', '--ask', 'n', '-n', '@world')
    sh.emerge('--quiet',        '--backtrack=130', '--usepkg=n', '--tree', '-u', '--ask', 'n', '-n', '@world')


def add_accept_keyword(*,
                       pkg: str,
                       verbose: bool,
                       debug: bool,
                       ):

    line = "={pkg} **".format(pkg=pkg)
    if verbose:
        ic(line)
    write_line_to_file(path=Path('/etc/portage/package.accept_keywords'),
                       line=line + '\n',
                       unique=True,
                       verbose=verbose,
                       debug=debug,)


def install_pkg(*,
                pkg: str,
                verbose: bool,
                debug: bool,
                ):
    #set +u
    #. /etc/profile
    #set -u
    ic(pkg)
    sh.emerge('--with-bdeps=y', '-pv',     '--tree', '--usepkg=n', '-u', '--ask', 'n', '-n', pkg)
    sh.emerge('--with-bdeps=y', '--quiet', '--tree', '--usepkg=n', '-u', '--ask', 'n', '-n', pkg)


def install_pkg_force(*,
                      pkg: str,
                      verbose: bool,
                      debug: bool,
                      ):
    #set +u
    #. /etc/profile
    #set -u
    ic(pkg)
    _env = {'CONFIG_PROTECT': '-*'}
    sh.emerge('--with-bdeps=y', '-pv',     '--tree', '--usepkg=n', '-u', '--ask', 'n', '--autounmask', '--autounmask-write', '-n', pkg, _env=_env)
    sh.emerge('--with-bdeps=y', '--quiet', '--tree', '--usepkg=n', '-u', '--ask', 'n', '--autounmask', '--autounmask-write', '-n', pkg, _env=_env)
    sh.emerge('--with-bdeps=y', '--quiet', '--tree', '--usepkg=n', '-u', '--ask', 'n', '--autounmask', '--autounmask-write', '-n', pkg, _env=_env)

