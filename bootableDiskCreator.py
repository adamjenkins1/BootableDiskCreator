#!/usr/bin/env python3
"""Contians class to automate process of creating bootable install media

This class is designed to create bootable install media with the intent of being accessible
from multiple Linux distributions without rendering the media unreadable
by Windows or OS X (using dd)

File name: bootableDiskCreator.py
Author: Adam Jenkins
Date created: 9/5/2018
Date last modified: ...
Python Version: 3.6.5
"""

from subprocess import Popen, PIPE
from getpass import getuser
from sys import exit as sysexit, stderr, stdout
import shutil
import os
import pwd

class BootableDiskCreator:
    """class that contains variables and methods to create a bootable drive"""
    totalBytes = 0
    totalBytesWritten = 0
    isoMount = '/mnt/iso/'
    target = '/mnt/target/'

    def __init__(self):
        """initializes member variables to default values"""
        self.totalBytes = 0
        self.totalBytesWritten = 0
        self.isoMount = '/mnt/iso/'
        self.target = '/mnt/target/'

    def progressCallback(self, bytesWritten):
        """prints percentange of image that has successfully been copied"""
        self.totalBytesWritten += bytesWritten
        stdout.write('copying image... {0:.2f}%\r'
                     .format(float(self.totalBytesWritten/self.totalBytes)*100))
        stdout.flush()

    def copyfileobj(self, fsrc, fdst, length=(16*1024)):
        """taken directly from shutil.copyfileobj

        this method is exactly the same as the library method except for the added
        progressCallback() function call to update users on how much of the image
        has been successfully copied
        """
        fsrc_read = fsrc.read
        fdst_write = fdst.write
        while True:
            buf = fsrc_read(length)
            if not buf:
                break
            fdst_write(buf)
            self.progressCallback(len(buf))

    def copyImage(self):
        """copies everything from the mounted image onto the mounted partition (except symlinks)"""
        # shutil.copytree() is used to preserve nested directories
        for entry in os.listdir(self.isoMount):
            isoEntry = self.isoMount + entry
            targetEntry = self.target + entry
            if os.path.islink(isoEntry):
                continue
            elif os.path.isdir(isoEntry):
                shutil.copytree(isoEntry, targetEntry)
            elif os.path.isfile(isoEntry):
                shutil.copy(isoEntry, self.target)

        # delete previous line from callback function
        stdout.write('\x1b[2K')
        print('copying image...done')

    def executeCommand(self, description, command):
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

    def getAvailablePartitions(self):
        """Creates and returns dictionary of partitions and their mountpoints"""
        # get list of partitions
        out = self.executeCommand('getting available partitions...',
                                  'lsblk -l | awk \'{if($6 == "part") {print $1","$7}}\'')

        # creates dictionary of partitions and their mount points (ex {'/dev/sdb1':'/mnt/target'})
        # if mount point is '', then partition is not mounted
        devices = {}
        for line in out.split('\n'):
            parts = line.split(',')
            devices[('/dev/' + parts[0])] = parts[1]

        return devices

    def validateInput(self, iso, device):
        """Validates user input and if input is correct, takes appropriate action"""
        # check if file provided has .iso extension
        if iso.split('.')[-1] != 'iso':
            sysexit('Error: \'{0}\' is not an ISO image'.format(iso))

        # check if image file provided exists
        if not os.path.isfile(iso):
            sysexit('Error: image \'{0}\' does not exist'.format(iso))

        devices = self.getAvailablePartitions()

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
            self.executeCommand('unmounting drive to be formated...', 'umount {0}'.format(device))

    def main(self, args):
        """Reads command line arguments, mounts image, and copies image files to given partition"""
        # check if script was executed with root privilages
        if pwd.getpwnam(getuser()).pw_uid != 0:
            sysexit('Error: must run as root')

        device = args.device
        iso = args.image


        # if optional mount point was provided, use it
        if args.image_mount:
            self.isoMount = args.image_mount

        if args.device_mount:
            self.target = args.device_mount


        # validates user input
        self.validateInput(iso, device)

        # if mount point does not exist, make it
        for mountPoint in [self.isoMount, self.target]:
            if not os.path.isdir(mountPoint):
                os.mkdir(mountPoint)

        # check if the image mount point is already in use
        if os.path.ismount(self.isoMount):
            self.executeCommand('unmounting previously mounted iso...',
                                'umount {0}'.format(self.isoMount))

        # mount iso image onto loop device
        self.executeCommand('mounting image...',
                            'mount -o loop {0} {1}'.format(iso, self.isoMount))

        # get size of mounted image
        self.totalBytes = int(self.executeCommand(
            'getting size of mounted image...',
            'du -sb {0} | awk \'{{print $1}}\''.format(self.isoMount)))

        # format given partition and then mount it
        self.executeCommand('formatting partition as fat32...',
                            'mkfs.fat -F32 -I {0}'.format(device))
        self.executeCommand('mouting {0} to {1}...'.format(device, self.target),
                            'mount {0} {1}'.format(device, self.target))

        # use overridden copy funtion which includes callback
        shutil.copyfileobj = self.copyfileobj

        self.copyImage()

        # final clean up
        self.executeCommand('unmounting image...', 'umount {0}'.format(self.isoMount))
        self.executeCommand('unmounting {0}...'.format(device), 'umount {0}'.format(device))
