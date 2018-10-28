#!/usr/bin/env python3
"""Contains main function to create BootableDiskCreator object and call class main method

File name: main.py
Author: Adam Jenkins
Date created: 9/17/2018
Date last modified: 10/27/18
Python Version: 3.6.5
"""

import argparse
from bootableDiskCreator import BootableDiskCreator

def main():
    """Sets up argument parser to parse command line arguments and calls class start method"""
    parser = argparse.ArgumentParser(description=('script to automate process of creating '
                                                  'bootable install media'))
    parser.add_argument('image', type=str, help='path to ISO image')
    parser.add_argument('device', type=str, help='partition on device to be written')
    parser.add_argument('--image-mount', type=str, help='mount point for ISO image')
    parser.add_argument('--device-mount', type=str, help='mount point for block device')
    parser.add_argument('--silent', default=False, action='store_true', help='suppress log output')

    bdc = BootableDiskCreator()
    bdc.start(parser.parse_args())

if __name__ == '__main__':
    main()
