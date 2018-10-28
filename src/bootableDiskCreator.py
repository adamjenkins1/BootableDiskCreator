#!/usr/bin/env python3
"""Contians class to automate process of creating bootable install media

This class is designed to create bootable install media with the intent of being accessible
from multiple Linux distributions without rendering the media unreadable
by Windows or OS X (using dd)

File name: bootableDiskCreator.py
Author: Adam Jenkins
Date created: 9/5/2018
Date last modified: 10/27/18
Python Version: 3.6.5
"""

from subprocess import Popen, PIPE
from getpass import getuser
from sys import stderr, stdout
import sys
import shutil
import os
import pwd
import threading

class BootableDiskCreator:
    """class that contains variables and methods to create a bootable drive"""

    class StringBuffer:
        """contains string which stores output normally written to stdout

        This string is then accessed by PyQt to display the logging output to the GUI
        instead of stdout. Access to BootableDiskCreator's instance of StringBuffer is thread safe.
        """
        def __init__(self):
            """initializes string to default value"""
            self.string = ''

        def write(self, string):
            """concatenates member variable with input"""
            self.string += string

        def read(self):
            """returns member variable value and resets it"""
            ret = self.string
            self.string = ''
            return ret

    def __init__(self):
        """initializes member variables to default values"""
        self.totalBytes = 0
        self.totalBytesWritten = 0
        self.isoMount = '/mnt/iso/'
        self.target = '/mnt/target/'
        self.buffer = self.StringBuffer()
        self.copyProgress = 0.0
        self.done = False
        self.thread = object()
        self.mutex = threading.Lock()
        self.iso = ''
        self.device = ''
        self.verbose = True

    def getStringBuffer(self):
        """locks thread while getting buffer and returns result"""
        ret = ''
        self.mutex.acquire()
        ret = self.buffer.read()
        self.mutex.release()
        return ret

    def progressCallback(self, bytesWritten):
        """prints percentange of image that has successfully been copied"""
        self.mutex.acquire()
        self.totalBytesWritten += bytesWritten
        self.copyProgress = float(self.totalBytesWritten/self.totalBytes)*100
        self.buffer.write('copying image... {0:.2f}%\n'.format(self.copyProgress))
        if self.verbose:
            stdout.write('copying image... {0:.2f}%\r'.format(self.copyProgress))
        self.mutex.release()
        stdout.flush()

    def copyfileobj(self, fsrc, fdst, length=(16*1024)):
        """taken directly from shutil.copyfileobj

        this method is exactly the same as the library method except for the added
        progressCallback() function call to update users on how much of the image
        has been successfully copied
        """
        fsrcRead = fsrc.read
        fdstWrite = fdst.write
        while True:
            buf = fsrcRead(length)
            if not buf:
                break
            fdstWrite(buf)
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
        if self.verbose:
            stdout.write('\x1b[2K')
            print('copying image...done')

    def executeCommand(self, description, command, logging=True):
        """Executes command given and exits if error is encountered"""
        if logging:
            self.mutex.acquire()
            self.buffer.write(description)
            self.mutex.release()

        if self.verbose:
            print(description, end='')

        process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        out = out[:-1].decode()
        err = err[:-1].decode()

        if process.returncode:
            print('fail\n\'{0}\' returned the following error:\n\'{1}\''.format(command, err),
                  file=stderr)
            sys.exit(process.returncode)

        if logging:
            self.mutex.acquire()
            self.buffer.write('done\n')
            self.mutex.release()

        if self.verbose:
            print('done')

        return out

    def getAvailablePartitions(self, logging=True):
        """Creates and returns dictionary of partitions and their mountpoints"""
        # get list of partitions
        out = self.executeCommand('getting available partitions...',
                                  'lsblk -l | awk \'{if($6 == "part") {print $1","$7}}\'', logging)

        # creates dictionary of partitions and their mount points (ex {'/dev/sdb1':'/mnt/target'})
        # if mount point is '', then partition is not mounted
        devices = {}
        for line in out.split('\n'):
            parts = line.split(',')
            devices[('/dev/' + parts[0])] = parts[1]

        return devices

    def validateInput(self, args):
        """Validates user input and if input is correct, takes appropriate action"""
        # check if script was executed with root privilages
        self.checkRoot()

        self.device = args.device
        self.iso = args.image
        self.verbose = not args.silent

        # if optional mount point was provided, use it
        if args.image_mount:
            self.isoMount = args.image_mount

        if args.device_mount:
            self.target = args.device_mount

        # check if file provided has .iso extension
        if self.iso.split('.')[-1] != 'iso':
            sys.exit('Error: \'{0}\' is not an ISO image'.format(self.iso))

        # check if image file provided exists
        if not os.path.isfile(self.iso):
            sys.exit('Error: image \'{0}\' does not exist'.format(self.iso))

        devices = self.getAvailablePartitions()

        # check if partition exists
        if self.device not in devices.keys():
            sys.exit('Error: partition \'{0}\' does not exist'.format(self.device))

        partitionStats = os.statvfs(self.device)

        if os.path.getsize(self.iso) > (partitionStats.f_bsize * partitionStats.f_blocks):
            sys.exit('Error: not enough space to copy \'{0}\' onto \'{1}\''
                     .format(self.iso, self.device))

        # check if partition is mounted as something important
        if devices[self.device] == '/' or '/boot' in devices[self.device]:
            sys.exit('Error: partition \'{0}\' currently mounted as \'{1}\''
                     .format(self.device, devices[self.device]))

        # check if user provided partition on same disk as OS and warn them
        osDisk = False
        choice = ''
        for key, value in devices.items():
            if self.device[:-1] in key and (value == '/' or '/boot' in value):
                osDisk = True

        if osDisk:
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
                sys.exit(0)

        # if device is mounted, unmount it
        if devices[self.device] != '':
            self.executeCommand('unmounting drive to be formated...',
                                'umount {0}'.format(self.device))

        # if mount point does not exist, make it
        for mountPoint in [self.isoMount, self.target]:
            if not os.path.isdir(mountPoint):
                os.mkdir(mountPoint)

    def checkRoot(self):
        """checks if script was executed with root privilages

        This is necessary because formating partitions and mounting devices requires
        root permissions
        """
        if pwd.getpwnam(getuser()).pw_uid != 0:
            sys.exit('Error: must run as root')

    def start(self, args):
        """validates user input and starts thread to create drive"""
        self.validateInput(args)

        self.thread = threading.Thread(target=self.main)
        self.thread.start()

    def main(self):
        """Reads command line arguments, mounts image, and copies image files to given partition"""
        self.done = False

        # check if the image mount point is already in use
        if os.path.ismount(self.isoMount):
            self.executeCommand('unmounting previously mounted iso...',
                                'umount {0}'.format(self.isoMount))

        # mount iso image onto loop device
        self.executeCommand('mounting image...',
                            'mount -o loop {0} {1}'.format(self.iso, self.isoMount))

        # get size of mounted image
        self.totalBytes = int(self.executeCommand(
            'getting size of mounted image...',
            'du -sb {0} | awk \'{{print $1}}\''.format(self.isoMount)))

        # format given partition and then mount it
        self.executeCommand('formatting partition as fat32...',
                            'mkfs.fat -F32 -I {0}'.format(self.device))
        self.executeCommand('mouting {0} to {1}...'.format(self.device, self.target),
                            'mount {0} {1}'.format(self.device, self.target))

        # use overridden copy funtion which includes callback
        shutil.copyfileobj = self.copyfileobj

        self.totalBytesWritten = 0
        self.copyImage()

        # final clean up
        self.executeCommand('unmounting image...', 'umount {0}'.format(self.isoMount))
        self.executeCommand('unmounting {0}...'.format(self.device),
                            'umount {0}'.format(self.device))
        self.done = True
