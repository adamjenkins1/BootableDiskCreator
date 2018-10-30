#!/usr/bin/env python3
"""Contians class to test functionality of BootableDiskCreator and DependencyChecker classes

File name: tests.py
Author: Adam Jenkins
Date created: 9/18/2018
Date last modified: 10/27/2018
Python Version: 3.6.5
"""

import pwd
import os
import threading
import shutil
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest import TestCase, mock
from unittest.mock import MagicMock
from bdc.bootableDiskCreator import BootableDiskCreator
from bdc.dependencyChecker import DependencyChecker

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
    @mock.patch('bdc.bootableDiskCreator.BootableDiskCreator.executeCommand')
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
    @mock.patch('bdc.bootableDiskCreator.BootableDiskCreator.executeCommand')
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
        self.assertEqual(err.exception.code, ('Error: not enough space to copy \'image.iso\' '
                                              'onto \'/dev/sdb1\''))

    @mock.patch('os.statvfs')
    @mock.patch('os.path.getsize')
    @mock.patch('os.path.isfile')
    @mock.patch('bdc.bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_mounted_as_parent_or_boot(self, mockPwd, mockExecute, mockFile,
                                                 mockImageSize, mockStats):
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
    @mock.patch('bdc.bootableDiskCreator.BootableDiskCreator.executeCommand')
    @mock.patch('pwd.getpwnam')
    def test_partition_on_primary_disk(self, mockPwd, mockExecute, mockFile, mockInput,
                                       mockImageSize, mockStats):
        """tests that warning is provided if given partition is on main disk"""
        mockPwd.return_value = MagicMock(pw_uid=0)
        mockExecute.return_value = 'sda1,/\nsda2,'
        mockFile.return_value = True
        mockInput.side_effect = ['asdf', 'no']
        mockImageSize.return_value = 1024**2
        mockStats.return_value = MagicMock(f_bsize=1024, f_blocks=1024)

        with self.assertRaises(SystemExit) as err:
            with redirect_stdout(StringIO()):
                self.obj.start(MagicMock(device='/dev/sda2', image='image.iso'))
        self.assertEqual(err.exception.code, 0)

    @mock.patch('os.statvfs')
    @mock.patch('os.path.getsize')
    @mock.patch('threading.Thread')
    @mock.patch('bdc.bootableDiskCreator.BootableDiskCreator.copyImage')
    @mock.patch('os.path.ismount')
    @mock.patch('os.path.isdir')
    @mock.patch('os.path.isfile')
    @mock.patch('bdc.bootableDiskCreator.BootableDiskCreator.executeCommand')
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

class DependencyCheckerTests(TestCase):
    """test class that inherits from unittest.TestCase class"""
    def setUp(self):
        """function to create new BootableDiskCreator object before each test"""
        self.obj = DependencyChecker()

    def tearDown(self):
        """function to delete BootableDiskCreator object after test finishes"""
        del self.obj

    @mock.patch('shutil.which')
    @mock.patch('sys.version_info')
    def test_bad_python_version(self, mockVersion, mockWhich):
        """tests Python version >= 3.5"""
        sys.modules['PyQt5'] = MagicMock()
        sys.modules['PyQt5'].Qt.PYQT_VERSION_STR = '5.11.3'
        mockVersion.major = 3
        mockVersion.minor = 3
        mockWhich.side_effect = ['/bin/awk', '/bin/mkfs.fat', '/bin/lsblk', '/bin/mount']

        with self.assertRaises(SystemExit) as err:
            self.obj.main()
        self.assertEqual(err.exception.code, 'Error: found Python 3.3, Python >= 3.5 required')

    @mock.patch('shutil.which')
    @mock.patch('sys.version_info')
    def test_missing_pyqt(self, mockVersion, mockWhich):
        """tests output if PyQt5 is missing"""
        sys.modules['PyQt5'] = None
        mockVersion.major = 3
        mockVersion.minor = 5
        mockWhich.side_effect = ['/bin/awk', '/bin/mkfs.fat', '/bin/lsblk', '/bin/mount']

        with self.assertRaises(SystemExit) as err:
            self.obj.main()
        self.assertEqual(err.exception.code, 'Error: missing required dependency: PyQt5')

    @mock.patch('shutil.which')
    @mock.patch('sys.version_info')
    def test_different_pyqt_version(self, mockVersion, mockWhich):
        """tests output if different version of PyQt5 is found"""
        sys.modules['PyQt5'] = MagicMock()
        sys.modules['PyQt5'].Qt.PYQT_VERSION_STR = 'FAKE_VERSION'
        mockVersion.major = 3
        mockVersion.minor = 5
        mockWhich.side_effect = ['/bin/awk', '/bin/mkfs.fat', '/bin/lsblk', '/bin/mount']

        output = StringIO()
        with redirect_stderr(output):
            self.obj.main()
        self.assertEqual(output.getvalue(), ('Warning: found PyQt5 FAKE_VERSION, this software '
                                             'has only been tested with PyQt5 5.11.3\n'))

    @mock.patch('shutil.which')
    @mock.patch('sys.version_info')
    def test_missing_bash_dependencies(self, mockVersion, mockWhich):
        """tests output if missing bash dependencies are found"""
        sys.modules['PyQt5'] = MagicMock()
        sys.modules['PyQt5'].Qt.PYQT_VERSION_STR = '5.11.3'
        mockVersion.major = 3
        mockVersion.minor = 5
        mockWhich.side_effect = [None, None, None, None]

        with self.assertRaises(SystemExit) as err:
            self.obj.main()
        self.assertEqual(err.exception.code, ('Error: missing required dependency: awk\nError: '
                                              'missing required dependency: mkfs.fat\nError: '
                                              'missing required dependency: lsblk\nError: '
                                              'missing required dependency: mount'))

    @mock.patch('shutil.which')
    @mock.patch('sys.version_info')
    def test_missing_everything(self, mockVersion, mockWhich):
        """tests output if all dependencies are missing"""
        sys.modules['PyQt5'] = None
        mockVersion.major = 3
        mockVersion.minor = 5
        mockWhich.side_effect = [None, None, None, None]

        with self.assertRaises(SystemExit) as err:
            self.obj.main()
        self.assertEqual(err.exception.code, 'Error: missing required dependency: PyQt5\n'
                                             'Error: missing required dependency: awk\nError: '
                                             'missing required dependency: mkfs.fat\nError: '
                                             'missing required dependency: lsblk\nError: '
                                             'missing required dependency: mount')
