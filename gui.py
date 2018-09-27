#!/usr/bin/env python3
from tkinter import (Tk, Frame, Button, Entry, Label, StringVar, 
        TclError, W, E, NSEW, SE, filedialog, Message, OptionMenu)
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
    partitionMenu = object()
    partitions = {}
    selectedPartition = object()

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.partitions = {}
        self.bdc = BootableDiskCreator()
        self.parent = parent
        self.iso = 'click "browse" to select the desired ISO image'
        self.partition = ''
        self.parent.title('Bootable Disk Creator GUI')
        self.isoDisplay = StringVar()
        self.isoDisplay.set(self.iso)
        self.selectedPartition = StringVar()
        self.selectedPartition.set('')

        # create wigits
        Message(self.parent, width=300, text=('Here\'s how to use this application:\n1. Select '
                                              'your ISO image\n2. Select the partition to be used\n'
                                              '3. Click "Go" and we\'ll handle the rest')
                                              ).grid(row=0, column=0, padx=20, ipady=20, sticky=W)
        Button(self.parent, text='Browse', command=self.selectISO).grid(row=1, column=1, sticky=W)
        Entry(self.parent, textvariable=self.isoDisplay, state='readonly', width=65).grid(row=1, column=0, padx=20, sticky=W)

        Label(self.parent, text='Select partition from drop down menu (you must select an ISO image first)').grid(row=2, column=0, padx=20, pady=(20, 0), sticky=W)
        self.partitionMenu = OptionMenu(self.parent, self.selectedPartition, '')
        self.partitionMenu.children['menu'].delete(0, 'end')
        self.partitionMenu.grid(row=3, column=0, padx=(20, 0), sticky=W)
        # this is really dumb, but I don't currently know of a way to stop tkinter from 
        # aligning columns, so I've put this button in the same column as the option menu
        # with extra padding. otherwise, it is aligned to the browse button, 
        # which isn't what I want
        Button(self.parent, text='Refresh Partitions', command=self.refreshPartitions).grid(row=3, column=0, padx=(150, 0), sticky=W)


        # call a dummy dialog with an impossible option to initialize the file
        # dialog without really getting a dialog window; this will throw a TclError
        try:
            self.parent.tk.call('tk_getOpenFile', '-foobarbaz')
        except TclError:
            pass
        self.parent.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
        self.parent.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')

        self.grid(row=1, column=0, columnspan=3, sticky=NSEW)

    def clearPartitionMenu(self):
        self.partitionMenu.children['menu'].delete(0, 'end')
        self.selectedPartition.set('')

    def refreshPartitions(self):
        if self.iso == 'click "browse" to select the desired ISO image':
            return 

        self.partitions = self.getAvailablePartitions()
        choices = list(self.partitions.keys())

        if len(choices) == 0:
            self.clearPartitionMenu()
        else: # len(choices) > 0
            self.selectedPartition.set(choices[0])
            self.partitionMenu = OptionMenu(self.parent, self.selectedPartition, *choices)
            self.partitionMenu.grid(row=3, column=0, padx=20, sticky=W)

        print(self.partitions)

    def selectISO(self):
        self.iso = filedialog.askopenfilename(initialdir = str(Path.home()),
                title = 'Select ISO image', 
                filetypes = (('ISO files', '*.iso'), ('all files', '*.*')))

        if str(self.iso) == '()' or self.iso == '':
            self.iso = 'click "browse" to select the desired ISO image'
            self.clearPartitionMenu()

        self.isoDisplay.set(self.iso)
        self.refreshPartitions()

        print(self.partitions)

    def getAvailablePartitions(self):
        self.suppressStdout()
        partitions = self.bdc.getAvailablePartitions()
        primary = ''
        for key, val in partitions.items():
            if val == '/' or '/boot' in val:
                primary = key[:-1]

        if primary != '':
            partitions = {key:val for (key, val) in partitions.items() if primary not in key}

        self.enableStdout()
        return partitions

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
