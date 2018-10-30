#!/usr/bin/env python3
import setuptools

with open('README.md', 'r') as f:
    longDescription = f.read()

setuptools.setup(
     name='bdc',  
     version='1.0.1',
     scripts=['src/bdc', 'src/bdc-gui'] ,
     author='Adam Jenkins',
     author_email='adamjenkins1701@gmail.com',
     description='bootable install media creator',
     long_description=longDescription,
     long_description_content_type='text/markdown',
     url='https://github.com/adamjenkins1/BootableDiskCreator',
     packages=setuptools.find_packages('src'),
     include_package_data=True,
     package_dir={'': 'src'},
     platforms="Linux",
     install_requires=['PyQt5==5.11.3'],
     python_requires='~=3.5',
     classifiers=[
         'Programming Language :: Python :: 3.5',
         'Programming Language :: Python :: 3.6',
         'License :: OSI Approved :: MIT License',
         'Operating System :: POSIX :: Linux',
     ],
 )
