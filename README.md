# Bootable Disk Creator [![Build Status](https://travis-ci.org/adamjenkins1/BootableDiskCreator.svg?branch=master)](https://travis-ci.org/adamjenkins1/BootableDiskCreator)

This project consists of a multithreaded GUI and CLI to automate the process of creating bootable install media in Linux. **NOTE: this project is still in development and has not been released. You can download the source and run the GUI or CLI, but an actual package has not been created yet.**

## Dependencies
* Python >= 3.5
* PyQt5 == 5.11.3
* awk
* mkfs.fat
* lsblk

## Usage
Until an actual package has been created, you'll have to download the source. This project requires root privilages (can't format or mount anything otherwise) so make sure to execute either script with `sudo` or as root.  To use the CLI:
```bash
./main.py </path/to/image.iso> </dev/partition>
```
For help and/or additional options
```bash
./main.py -h
```

The GUI doesn't take any command line arguments so you can run it like so:
```bash
./pyqt.py
```
You can run the unit tests with the Python unittest library
```bash
python3 -m unittest tests.py
```
Or with pytest
```bash
pytest tests.py
```

### How it works
A lot of Python. This project uses Python for all of the heavy lifting and bash when Python isn't the right tool. Bash commands are executed from Python using `subprocess.Popen()`. This project will do the following to create the bootable drive:
1. get a list of available partitions
2. mount the provided image as a loop device
3. format the provided partition as FAT32
4. mount the partition
5. copy all the data onto that partition (excluding symlinks. not supported by FAT32)

The drive is then unmounted and you're left with your very own bootable drive. There is a catch however. *This project will **not** install a boot loader or set any flags to support legacy boot. The drive created is UEFI bootable only.* This is subject to change, so don't get your hopes up if you have a machine that doesn't support UEFI or have an image that doesn't have a boot loader already installed. A lot of images come with boot loaders installed, so if you're unsure whether or not your image has a boot loader, the it probably does (unless it's [DBAN](https://dban.org/)). You can always mount the image and look at it yourself you want to be doubly sure. 

### Why build this?
I came up with the idea while I was preparing my craptop for [DEF CON 26](https://www.defcon.org/) and I was having trouble creating the bootable media to install Linux. I was using a Macbook at the time (not by choice, if I had my way, we'd all be using Linux) and the tools for creating bootable install media on Mac are not great, and there isn't anything reliable accross multiple Linux distributions. What makes this project different than other tools out there is that this one does not use `dd` to write the image onto the drive. This preserves the file system on the drive and allows it to be read from other operating systems. A lot of tools will use `dd` to manually write the bytes because it's quick and easy.  The problem with this is that it makes your drive look like an ISO file system, which other operating systems can't read. Essentially with this method, a bootable drive is created, but that's all you can do with it, which didn't seem ideal to me.
