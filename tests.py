#!/usr/bin/env python3
from unittest import TestCase, mock
from unittest.mock import MagicMock
from bootableDiskCreator import BootableDiskCreator
import pwd

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

