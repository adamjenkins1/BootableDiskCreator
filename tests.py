#!/usr/bin/env python3
from unittest import TestCase, mock
from unittest.mock import MagicMock
from bootableDiskCreator import BootableDiskCreator
import pwd
import os

class BootableDiskCreatorTests(TestCase):
    def setUp(self):
        self.obj = BootableDiskCreator()

    def tearDown(self):
        del self.obj

    @mock.patch('pwd.getpwnam')
    def test_root_user(self, mockPwd):
        mockPwd.return_value = MagicMock(pw_uid=1)
        with self.assertRaises(SystemExit) as err:
            self.obj.main(MagicMock(device='/dev/sdb1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: must run as root')

    @mock.patch('pwd.getpwnam')
    def test_image_exists(self, mockPwd):
        mockPwd.return_value = MagicMock(pw_uid=0)
        with self.assertRaises(SystemExit) as err:
            self.obj.main(MagicMock(device='/dev/sdb1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: image \'image.iso\' does not exist')

    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_exists(self, mockPwd, mockExecute, mockFile):
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sda1,/'
        mockFile.return_value = True
        with self.assertRaises(SystemExit) as err:
            self.obj.main(MagicMock(device='/dev/sdb1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: partition \'/dev/sdb1\' does not exist')

    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_mounted_as_parent(self, mockPwd, mockExecute, mockFile):
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sda1,/'
        mockFile.return_value = True
        with self.assertRaises(SystemExit) as err:
            self.obj.main(MagicMock(device='/dev/sda1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: partition \'/dev/sda1\' currently mounted as \'/\'')

    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_mounted_as_boot(self, mockPwd, mockExecute, mockFile):
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sda1,/boot'
        mockFile.return_value = True
        with self.assertRaises(SystemExit) as err:
            self.obj.main(MagicMock(device='/dev/sda1', image='image.iso'))
        self.assertEqual(err.exception.code, 'Error: partition \'/dev/sda1\' currently mounted as \'/boot\'')

    @mock.patch('builtins.input')
    @mock.patch('os.path.isfile')
    @mock.patch('bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_on_primary_disk(self, mockPwd, mockExecute, mockFile, mockInput):
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sda1,/\nsda2,'
        mockFile.return_value = True
        mockInput.side_effect = ['asdf', 'no']

        with self.assertRaises(SystemExit) as err:
            self.obj.main(MagicMock(device='/dev/sda2', image='image.iso'))
        self.assertEqual(err.exception.code, 0)
