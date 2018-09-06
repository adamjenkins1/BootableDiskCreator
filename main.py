#!/usr/bin/env python3
from subprocess import Popen, PIPE
from getpass import getuser
from pwd import getpwnam
from sys import exit as sysexit, stderr
import shutil
import os

def executeCommand(description, command):
    """Executes command given and exits if error is encountered"""
    print(description, end='')
    process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = process.communicate()
    out = out[:-1].decode()
    err = err[:-1].decode()

    if process.returncode:
        print('fail\n\'{0}\' returned the following error:\n\'{1}\''.format(command, err),
              file=stderr)
        sysexit(process.returncode)

    print('done')
    return out

def main():
    if getpwnam(getuser()).pw_uid != 0:
        print('Error: must run as root', file=stderr)
        sysexit(1)

    isoMount = '/mnt/iso/'
    target = '/mnt/lexar/'
    device = '/dev/sdb1'
    if not os.path.isdir(isoMount):
        os.mkdir(isoMount)

    if os.path.ismount(isoMount):
        executeCommand('unmounting previously mounted iso...', 'umount {0}'.format(isoMount))

    executeCommand('mounting iso...',
                   ('mount -o loop '
                    '/home/adam/Downloads/clonezilla-live-2.5.6-22-amd64.iso '
                    '{0}').format(isoMount))

    out = executeCommand('getting current mounted volumes...', 'mount -l')
    mounts = []
    for line in out.split('\n'):
        mounts.append(line.split(' ')[0])

    if device in mounts:
        executeCommand('unmounting drive to be formated...', 'umount {0}'.format(device))

    executeCommand('formatting partition as fat32...', 'mkfs.fat -F32 -I {0}'.format(device))
    executeCommand('mouting {0} to {1}...'.format(device, target),
                   'mount {0} {1}'.format(device, target))

    print('copying files...', end='')
    for i in os.listdir(isoMount):
        isoEntry = isoMount + i
        targetEntry = target + i
        if os.path.isdir(isoEntry):
            shutil.copytree(isoEntry, targetEntry)
        elif os.path.isfile(isoEntry):
            shutil.copy2(isoEntry, target)
    print('done')

    executeCommand('unmounting {0}...'.format(device), 'umount {0}'.format(device))

if __name__ == '__main__':
    main()
