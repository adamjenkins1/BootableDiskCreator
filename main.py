#!/usr/bin/env python3
from subprocess import Popen, PIPE, DEVNULL
from getpass import getuser
from pwd import getpwnam
from sys import exit, stderr
import shutil
import os

def executeCommand(description, command):
    """Executes command given and exits if error is encountered"""
    print(description, end='')
    process = Popen(command, stdout=DEVNULL, stderr=PIPE, shell=True)
    err = process.communicate()[1].decode()
    if process.returncode:
        print('fail\n\'{0}\' returned the following error:\n\'{1}\''.format(command, err[:-1]), file=stderr)
        exit(process.returncode)
    print('done')

if getpwnam(getuser()).pw_uid != 0:
    print('Error: must run as root', file=stderr)
    exit(1)

if not os.path.isdir('/mnt/iso'):
    os.mkdir('/mnt/iso')

if os.path.ismount('/mnt/iso'):
    executeCommand('unmounting previously mounted iso...', 'umount /mnt/iso')

executeCommand('mounting iso...', 'mount -o loop /home/adam/Downloads/clonezilla-live-2.5.6-22-amd64.iso /mnt/iso')

p = Popen(['mount', '-l'], stdout=PIPE, stderr=PIPE)
out, err = p.communicate()
out = out[:-1].decode()
mounts = []
for line in out.split('\n'):
    mounts.append(line.split(' ')[0])

if '/dev/sdc1' in mounts:
    executeCommand('unmounting drive to be formated...', 'umount /dev/sdc1')

executeCommand('formatting partition as fat32...', 'mkfs.fat -F32 -I /dev/sdc1')
print('copying files...', end='')
shutil.copytree('/mnt/iso/', '/mnt/test')
print('done')
