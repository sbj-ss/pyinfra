# pyinfra
# File: pyinfra/facts/server.py
# Desc: server/os related facts

import re

from dateutil.parser import parse as parse_date

from pyinfra.api import FactBase


class Home(FactBase):
    command = 'echo $HOME'


class Hostname(FactBase):
    command = 'hostname'


class Os(FactBase):
    command = 'uname -s'


class OsVersion(FactBase):
    command = 'uname -r'


class Arch(FactBase):
    command = 'uname -p'


class Date(FactBase):
    '''Returns the current datetime on the server.'''

    command = 'date'

    @classmethod
    def process(cls, output):
        return parse_date(output[0])


class Users(FactBase):
    '''
    Gets & returns a dict of users -> details:

    .. code:: python

        'user_name': {
            'home': '/home/user_name',
            'shell': '/bin/bash,
            'group': 'main_user_group',
            'groups': [
                'other',
                'groups'
            ]
        },
        ...
    '''

    command = '''
        for i in `cat /etc/passwd | cut -d: -f1`; do
            ID=`id $i`
            META=`cat /etc/passwd | grep ^$i: | cut -d: -f6-7`
            echo $ID$META
        done
    '''

    _regex = r'^uid=[0-9]+\(([a-z\-]+)\) gid=[0-9]+\(([a-z\-]+)\) groups=([,0-9a-z\-\(\)]+)(.*)$'
    _group_regex = r'^[0-9]+\(([a-z\-]+)\)$'

    @classmethod
    def process(cls, output):
        users = {}
        for line in output:
            matches = re.match(cls._regex, line)

            if matches:
                # Parse out the home/shell
                home_shell = matches.group(4)
                home = shell = None

                # /blah: is just a home
                if home_shell.endswith(':'):
                    home = home_shell[:1]

                # :/blah is just a shell
                elif home_shell.startswith(':'):
                    shell = home_shell[1:]

                # Both home & shell
                elif ':' in home_shell:
                    home, shell = home_shell.split(':')

                # Main user group
                group = matches.group(2)

                # Parse the groups
                groups = []
                for group_matches in matches.group(3).split(','):
                    name = re.match(cls._group_regex, group_matches).group(1)
                    # We only want secondary groups here
                    if name != group:
                        groups.append(
                            name
                        )

                users[matches.group(1)] = {
                    'group': group,
                    'groups': groups,
                    'home': home,
                    'shell': shell
                }

        return users


class LinuxDistribution(FactBase):
    '''
    Returns a dict of the Linux distribution version. Ubuntu, CentOS & Debian currently:

    .. code:: python

        {
            'name': 'CentOS',
            'major': 6,
            'minor': 5
        }
    '''

    command = 'cat /etc/*-release'

    # Currently supported distros
    _regexes = [
        r'(Ubuntu) ([0-9]{2})\.([0-9]{2})',
        r'(CentOS) release ([0-9]).([0-9])',
        r'(CentOS) Linux release ([0-9]).([0-9])',
        r'(Debian) GNU/Linux ([0-9])()'
    ]

    @classmethod
    def process(cls, output):
        output = '\n'.join(output)

        for regex in cls._regexes:
            matches = re.search(regex, output)
            if matches:
                return {
                    'name': matches.group(1),
                    'major': matches.group(2),
                    'minor': matches.group(3)
                }

        return {'name': 'Unknown'}
