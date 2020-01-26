from __future__ import unicode_literals

import re
from datetime import datetime


# examples from c:\Windows
# d-----        1/25/2020  10:27 AM                WinSxS
# d-r---       11/15/2019   6:39 AM                PrintDialog
# d-r-s-        9/15/2018  12:19 AM                media
# -a----        9/15/2018  12:12 AM          78848 bfsvc.exe
# -a--s-        1/25/2020   8:19 AM          67584 bootstat.dat
WIN_LS_REGEX = re.compile((
    # filetype and mode
    r'^([darhs\-]{6})\s+'
    # Windows date
    r'([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4})\s+([0-9]{1,2}:[0-9]{1,2}\s[AP][M])\s+'
    # Size (Note: no size on directories)
    r'([0-9]+)\s+'
    # Size and Filename
    r'([\w\/\.@-]+)'
))

WIN_FLAG_TO_TYPE = {
    'd': 'directory',
    '-': 'file',
}

WIN_FLAG_TO_ATTR = {
    'a': 'archive',
    'r': 'readonly',
    'h': 'hidden',
    's': 'system',
    '-': 'none',
}


def _parse_time(time):
    # Try matching windows format
    try:
        tmp = datetime.strptime(time, '%m/%d/%Y %H:%M %p')
        return tmp
    except ValueError:
        pass


def parse_win_ls_output(output, wanted_type):
    if output:
        matches = re.match(WIN_LS_REGEX, output)
        if matches:

            type = WIN_FLAG_TO_TYPE[output[0]]

            if type != wanted_type:
                return False

            hidden = False
            system = False
            readonly = False
            archive = False

            mode_without_first = matches.group(1)[1:]

            for c in mode_without_first:
                tmp = WIN_FLAG_TO_ATTR[c]
                if tmp != 'none':
                    if tmp == 'hidden':
                        hidden = True
                    if tmp == 'readonly':
                        readonly = True
                    if tmp == 'archive':
                        archive = True
                    if tmp == 'system':
                        system = True


            mode = {
                'archive': archive,
                'hidden': hidden,
                'readonly': readonly,
                'system': system,
            }

            date_and_time = '{} {}'.format(matches.group(2), matches.group(3))

            size = "0"
            if type == 'file':
                size = matches.group(4)

            out = {
                'type': type,
                'mode': mode,
                'mtime': _parse_time(date_and_time),
                'size': size,
                'name': matches.group(5),
                # TODO: link
            }

            return out
