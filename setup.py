#!/usr/bin/env python3
import setuptools
import os

with open('README.md', 'r') as f:
    longDescription = f.read()

with open(os.path.join(os.path.dirname(__file__), 'src', 'bdc', '__init__.py')) as f:
    exec(f.read())

setuptools.setup(
     name=__name__,
     version=__version__,
     scripts=['src/bdc/bdc', 'src/bdc/bdc-gui'] ,
     author=__author__,
     author_email='adamjenkins1701@gmail.com',
     description='bootable install media creator',
     long_description=longDescription,
     long_description_content_type='text/markdown',
     url=__url__,
     packages=['bdc'],
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
