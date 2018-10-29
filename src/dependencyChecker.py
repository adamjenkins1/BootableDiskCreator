#!/usr/bin/env python3
"""Contains class to check required dependencies for BootableDiskCreator CLI and GUI

File name: dependencyChecker.py
Author: Adam Jenkins
Date created: 10/28/18
Date last modified: 10/28/18
Python Version: 3.6.5
"""
import sys
import shutil

class DependencyChecker:
    """class to check BootableDiskCreator dependencies"""
    def __init__(self):
        """initializes member variables"""
        self.bashDependencies = ['awk', 'mkfs.fat', 'lsblk', 'mount']
        self.PyQtVersion = '5.11.3'
        self.errors = ''
        self.PyQtInstall = False

    def main(self):
        """method to check if dependencies are satisfied"""
        if not (sys.version_info.major == 3 and sys.version_info.minor >= 5):
            self.errors += ('Error: found Python {}.{}, Python >= 3.5 required\n'
                            .format(sys.version_info.major, sys.version_info.minor))

        try:
            import PyQt5
            self.PyQtInstall = True
        except ImportError:
            self.errors += 'Error: missing required dependency: PyQt5\n'

        if self.PyQtInstall:
            from PyQt5 import Qt
            if Qt.PYQT_VERSION_STR != self.PyQtVersion:
                print('Warning: found PyQt5 {}, this software has only been tested with PyQt5 {}'
                      .format(Qt.PYQT_VERSION_STR, self.PyQtVersion), file=sys.stderr)

        for i in self.bashDependencies:
            if shutil.which(i) is None:
                self.errors += 'Error: missing required dependency: {}\n'.format(i)

        if self.errors:
            sys.exit(self.errors[:-1])
