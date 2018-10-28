#!/usr/bin/env python3
"""Contians class to test functionality of BootableDiskCreator class

File name: tests.py
Author: Adam Jenkins
Date created: 9/18/2018
Date last modified: 10/27/2018
Python Version: 3.6.5
"""

import pwd
import os
import threading
from unittest import TestCase, mock
from unittest.mock import MagicMock
from bootableDiskCreator import BootableDiskCreator

class BootableDiskCreatorTests(TestCase):
    """test class that inherits from unittest.TestCase class"""
    def setUp(self):
        """function to create new BootableDiskCreator object before each test"""
        self.obj = BootableDiskCreator()

    def tearDown(self):
        """function to delete BootableDiskCreator object after test finishes"""
        del self.obj

    @mock.patch('pwd.getpwnam')
    def test_root_user(self, mockPwd):
        """tests whether or not script was executed as root"""
        mockPwd.return_value = MagicMock(pw_uid=1)
        with self.assertRaises(SystemExit) as err:
            self.obj.start(MagicMock(device='/dev/sdb1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: must run as root')

    @mock.patch('pwd.getpwnam')
    def test_bad_image(self, mockPwd):
        """tests if the provided image exists"""
        mockPwd.return_value = MagicMock(pw_uid=0)
        with self.assertRaises(SystemExit) as err:
            self.obj.start(MagicMock(device='/dev/sdb1', image='image.asdf'))
        self.assertEqual(err.exception.code, 'Error: \'image.asdf\' is not an ISO image')

    @mock.patch('pwd.getpwnam')
    def test_image_exists(self, mockPwd):
        """tests if the provided image exists"""
        mockPwd.return_value = MagicMock(pw_uid=0)
        with self.assertRaises(SystemExit) as err:
            self.obj.start(MagicMock(device='/dev/sdb1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: image \'image.iso\' does not exist')

    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_exists(self, mockPwd, mockExecute, mockFile):
        """tests if the given partition exists"""
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sda1,/'
        mockFile.return_value = True
        with self.assertRaises(SystemExit) as err:
            self.obj.start(MagicMock(device='/dev/sdb1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: partition \'/dev/sdb1\' does not exist')

    @mock.patch('os.statvfs')
    @mock.patch('os.path.getsize')
    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_too_small(self, mockPwd, mockExecute, mockFile, mockImageSize, mockStats):
        """tests if the given partition exists"""
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sdb1,'
        mockFile.return_value = True
        mockImageSize.return_value = 1024**2
        mockStats.return_value = MagicMock(f_bsize=1024, f_blocks=1)
        with self.assertRaises(SystemExit) as err:
            self.obj.start(MagicMock(device='/dev/sdb1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: not enough space to copy \'image.iso\' onto \'/dev/sdb1\'')

    @mock.patch('os.statvfs')
    @mock.patch('os.path.getsize')
    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_mounted_as_parent_or_boot(self, mockPwd, mockExecute, mockFile, mockImageSize, mockStats):
        """tests if then given partition is mounted as something important"""
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sda1,/'
        mockFile.return_value = True
        mockImageSize.return_value = 1024**2
        mockStats.return_value = MagicMock(f_bsize=1024, f_blocks=1024)
        with self.assertRaises(SystemExit) as err:
            self.obj.start(MagicMock(device='/dev/sda1', image='image.iso'))
        self.assertEqual(err.exception.code,
                         'Error: partition \'/dev/sda1\' currently mounted as \'/\'')

        mockExecute.return_value = 'sda1,/boot'
        with self.assertRaises(SystemExit) as err:
            self.obj.start(MagicMock(device='/dev/sda1', image='image.iso'))
        self.assertEqual(err.exception.code,
                         'Error: partition \'/dev/sda1\' currently mounted as \'/boot\'')

    @mock.patch('os.statvfs')
    @mock.patch('os.path.getsize')
    @mock.patch('builtins.input')
    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_on_primary_disk(self, mockPwd, mockExecute, mockFile, mockInput, mockImageSize, mockStats):
        """tests that warning is provided if given partition is on main disk"""
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sda1,/\nsda2,'
        mockFile.return_value = True
        mockInput.side_effect = ['asdf', 'no']
        mockImageSize.return_value = 1024**2
        mockStats.return_value = MagicMock(f_bsize=1024, f_blocks=1024)

        with self.assertRaises(SystemExit) as err:
            self.obj.start(MagicMock(device='/dev/sda2', image='image.iso'))
        self.assertEqual(err.exception.code, 0)

    @mock.patch('os.statvfs')
    @mock.patch('os.path.getsize')
    @mock.patch('threading.Thread')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.copyImage')
    @mock.patch('os.path.ismount')
    @mock.patch('os.path.isdir')
    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_create_bootable_drive(self, mockPwd, mockExecute, mockFile, mockDir,
                                   mockMount, mockCopy, mockThread, mockImageSize, mockStats):
        """tests functionality of creating a bootable drive"""
        mockThread.start = self.obj.main()
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.side_effect = ['sda1,/\nsdb1,/mnt/fakemount', '', '', '', 5000, '', '', '', '']
        mockFile.return_value = True
        mockDir.return_value = True
        mockMount.return_value = True
        mockImageSize.return_value = 1024**2
        mockStats.return_value = MagicMock(f_bsize=1024, f_blocks=1024)

        self.assertEqual(self.obj.start(MagicMock(device='/dev/sdb1', image='image.iso')), None)
