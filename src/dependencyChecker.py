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
        self.bashDependencies = ['awk', 'mkfs.fat', 'lsblk']
        self.PyQtVersion = '5.11.3'

    def main(self):
        """method to check if dependencies are satisfied"""
        if not (sys.version_info.major == 3 and sys.version_info.minor >= 5):
            sys.exit('Error: found Python {}.{}, Python >= 3.5 required'
                     .format(sys.version_info.major, sys.version_info.minor))

        for i in self.bashDependencies:
            if shutil.which(i) is None:
                sys.exit('Error: missing required dependency: {}'.format(i))

        try:
            import PyQt5
        except ImportError:
            sys.exit('Error: missing required dependency: PyQt5')

        from PyQt5 import Qt

        if Qt.PYQT_VERSION_STR != self.PyQtVersion:
            print('Warning: found PyQt5 {}, this software has only been tested with PyQt5 {}'
                  .format(Qt.PYQT_VERSION_STR, self.PyQtVersion), file=sys.stderr)
