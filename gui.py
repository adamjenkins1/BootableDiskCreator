#!/usr/bin/env python3
from tkinter import (Tk, Frame, Button, Entry, Label, StringVar, 
        TclError, W, NSEW, filedialog, Message)
from pathlib import Path
from bootableDiskCreator import BootableDiskCreator
import sys
import os

class GUI(Frame):
    parent = object()
    iso = ''
    partition = ''
    isoDisplay = object()
    bdc = object()

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.bdc = BootableDiskCreator()
        self.parent = parent
        self.iso = ''
        self.partition = ''
        self.parent.title('Bootable Disk Creator GUI')
        self.isoDisplay = StringVar()
        self.isoDisplay.set('click "browse" to select the desired ISO image')

        # create wigits
        Button(self.parent, text='Browse', command=self.selectISO).grid(row=1, column=1, sticky=W)
        Entry(self.parent, textvariable=self.isoDisplay, state='readonly', width=65).grid(row=1, column=0, padx=20, sticky=W)
        Message(self.parent, width=300, text=('Here\'s how to use this application:\n1. Select '
                                              'your ISO image\n2.Select the partition to be used\n'
                                              '3. Click "Go" and we\'ll handle the rest')
                                              ).grid(row=0, column=0, padx=20, ipady=20, sticky=W)


        # call a dummy dialog with an impossible option to initialize the file
        # dialog without really getting a dialog window; this will throw a TclError
        try:
            self.parent.tk.call('tk_getOpenFile', '-foobarbaz')
        except TclError:
            pass
        self.parent.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
        self.parent.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')

        self.grid(row=1, column=0, columnspan=3, sticky=NSEW)

    def selectISO(self):
        self.iso = filedialog.askopenfilename(initialdir = str(Path.home()),
                title = 'Select ISO image', 
                filetypes = (('ISO files', '*.iso'), ('all files', '*.*')))

        if str(self.iso) == '()' or self.iso == '':
            self.iso = 'click "browse" to select the desired ISO image'

        self.isoDisplay.set(self.iso)

        self.suppressStdout()
        partitions = self.bdc.getAvailablePartitions()
        self.enableStdout()
        print(partitions)

    def suppressStdout(self):
        sys.stdout = open(os.devnull, 'w')

    def enableStdout(self):
        sys.stdout = sys.__stdout__

def main():
    root = Tk()
    g = GUI(root)
    root.geometry('660x560')
    root.mainloop()

if __name__ == '__main__':
    main()
