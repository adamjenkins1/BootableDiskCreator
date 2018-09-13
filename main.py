#!/usr/bin/env python3
"""Automates process of creating bootable install media

This script is designed to create bootable install media with the intent of being accessible
from multiple Linux distributions without rendering the media unreadable by Windows or OS X

File name: main.py
Author: Adam Jenkins
Date created: 9/5/2018
Date last modified: ...
Python Version: 3.6.5
"""

from subprocess import Popen, PIPE
from getpass import getuser
from pwd import getpwnam
from sys import exit as sysexit, stderr
import shutil
import os
import argparse

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

def validateInput(iso, device):
    """Validates user input and if input is correct, takes appropriate action"""
    # check if image file provided exists
    if not os.path.isfile(iso):
        sysexit('Error: image \'{0}\' does not exist'.format(iso))

    # get list of partitions
    out = executeCommand('getting available partitions...',
                         'lsblk -l | awk \'{if($6 == "part") {print $1","$7}}\'')

    # creates dictionary of partitions and their mount points (ex {'/dev/sdb1':'/mnt/target'})
    # if mount point is '', then partition is not mounted
    devices = {}
    for line in out.split('\n'):
        parts = line.split(',')
        devices[('/dev/' + parts[0])] = parts[1]

    # check if partition exists
    if device not in devices.keys():
        sysexit('Error: partition \'{0}\' does not exist'.format(device))

    # check if partition is mounted as something important
    if devices[device] == '/' or '/boot' in devices[device]:
        sysexit('Error: partition \'{0}\' currently mounted as \'{1}\''
                .format(device, devices[device]))

    # check if user provided partition on same disk as OS and warn them
    OSDisk = False
    choice = ''
    for key, value in devices.items():
        if device[:-1] in key and (value == '/' or '/boot' in value):
            OSDisk = True

    if OSDisk:
        print(('Warning: it looks like the given partition is on the same disk as your OS.\n'
               'This utility is designed to create REMOVABLE install media, but will'
               ' format any\npartition if it is available. However, creating bootable install'
               ' media using a\npartition on your primary disk is not recommended.'
               '\nDo you wish to continue? [yes/No]'), end=' ')
        choice = input()
        while choice.lower() != 'yes' and choice.lower() != 'no':
            print(('Unrecognized choice. '
                   'Please type \'yes\' to continue or \'no\' to exit. [yes/No]'), end=' ')
            choice = input()

        if choice.lower() != 'yes':
            sysexit(0)

    # if device is mounted, unmount it
    if devices[device] != '':
        executeCommand('unmounting drive to be formated...', 'umount {0}'.format(device))

def main():
    """Reads command line arguments, mounts image, and copies image files to given partition"""
    # check if script was executed with root privilages
    if getpwnam(getuser()).pw_uid != 0:
        sysexit('Error: must run as root')

    # setup argument parser
    parser = argparse.ArgumentParser(description=('script to automate process of creating '
                                                  'bootable install media'))
    parser.add_argument('image', type=str, help='path to ISO image')
    parser.add_argument('device', type=str, help='partition on device to be written')
    parser.add_argument('--image-mount', type=str, help='mount point for ISO image')
    parser.add_argument('--device-mount', type=str, help='mount point for block device')
    args = parser.parse_args()

    device = args.device
    iso = args.image

    # default values for mount points
    isoMount = '/mnt/iso/'
    target = '/mnt/target/'

    # if optional mount point was provided, use it
    if args.image_mount:
        isoMount = args.image_mount

    if args.device_mount:
        target = args.device_mount

    # validates user input
    validateInput(iso, device)

    # if mount point does not exist, make it
    for mountPoint in [isoMount, target]:
        if not os.path.isdir(mountPoint):
            os.mkdir(mountPoint)

    # check if the image mount point is already in use
    if os.path.ismount(isoMount):
        executeCommand('unmounting previously mounted iso...', 'umount {0}'.format(isoMount))

    # mount iso image onto loop device
    executeCommand('mounting image...',
                   ('mount -o loop {0} {1}').format(iso, isoMount))

    # format given partition and then mount it
    executeCommand('formatting partition as fat32...', 'mkfs.fat -F32 -I {0}'.format(device))
    executeCommand('mouting {0} to {1}...'.format(device, target),
                   'mount {0} {1}'.format(device, target))

    # copy everything from the mounted image
    # shutil.copytree() is used to preserve nested directories
    print('copying files...', end='')
    for entry in os.listdir(isoMount):
        isoEntry = isoMount + entry
        targetEntry = target + entry
        if os.path.islink(isoEntry):
            continue
        elif os.path.isdir(isoEntry):
            shutil.copytree(isoEntry, targetEntry)
        elif os.path.isfile(isoEntry):
            shutil.copy2(isoEntry, target)
    print('done')

    # final clean up
    executeCommand('unmounting image...', 'umount {0}'.format(isoMount))
    executeCommand('unmounting {0}...'.format(device), 'umount {0}'.format(device))

if __name__ == '__main__':
    main()
