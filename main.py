#!/usr/bin/env python3
"""Contains main function to create BootableDiskCreator object and call class main method

File name: main.py
Author: Adam Jenkins
Date created: 9/17/2018
Date last modified: ...
Python Version: 3.6.5
"""

import argparse
from bootableDiskCreator import BootableDiskCreator

def main():
    """Sets up argument parser to parse command line arguments and calls class main method"""
    parser = argparse.ArgumentParser(description=('script to automate process of creating '
                                                  'bootable install media'))
    parser.add_argument('image', type=str, help='path to ISO image')
    parser.add_argument('device', type=str, help='partition on device to be written')
    parser.add_argument('--image-mount', type=str, help='mount point for ISO image')
    parser.add_argument('--device-mount', type=str, help='mount point for block device')

    b = BootableDiskCreator()
    b.start(parser.parse_args())

if __name__ == '__main__':
    main()
