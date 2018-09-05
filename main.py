#!/usr/bin/env python3
import os
from subprocess import Popen, PIPE, DEVNULL
import sys
import pwd
import getpass

def executeCommand(description, command):
    """Executes command given and exits if error is encountered"""
    print(description, end='')
    process = Popen(command, stdout=DEVNULL, stderr=PIPE, shell=True)
    err = process.communicate()[1].decode()
    if process.returncode:
        print('fail\n\'{0}\' returned the following error:\n\'{1}\''.format(command, err[:-1]))
        sys.exit(process.returncode)
    print('done')

if pwd.getpwnam(getpass.getuser()).pw_uid != 0:
    print('Error: must run as root', file=sys.stderr)
    sys.exit(1)

if not os.path.isdir('/mnt/iso'):
    os.mkdir('/mnt/iso')

executeCommand('mounting iso...', 'mount -o loop /home/adam/Downloads/clonezilla-live-2.5.6-22-amd64.iso /mnt/iso')
