#!/usr/bin/env python3


import click
from portagetool import get_use_flags_for_package

MESA_FLAGS = get_use_flags_for_package(package='media-libs/mesa',
                                       verbose=False,
                                       debug=False,)
MESA_FLAGS.append('video_cards_panfrost')  # https://github.com/Jannik2099/gentoo-pinebookpro/blob/master/mesa


# https://stackoverflow.com/questions/40182157/python-click-shared-options-and-flags-between-commands
def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


click_mesa_options = [
    click.option('--mesa-use-enable', is_flag=False, required=False, type=click.Choice(MESA_FLAGS), default=["gallium"], multiple=True),
    click.option('--mesa-use-disable', is_flag=False, required=False, type=click.Choice(MESA_FLAGS), default=["osmesa", 'llvm'], multiple=True),
]
