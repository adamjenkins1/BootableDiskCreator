#!/usr/bin/env python3
from tkinter import *
from tkinter import filedialog
from pathlib import Path

class GUI(Frame):
    canvas = object()
    parent = object()
    iso = ''
    partition = ''
    isoDisplay = object()

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.iso = ''
        self.partition = ''
        self.parent.title('Bootable Disk Creator GUI')
        Button(self.parent, text='select ISO', command=self.selectISO).pack(padx=5, pady=5, expand=1)
        self.isoDisplay = StringVar()
        Entry(self.parent, textvariable=self.isoDisplay).pack()
        self.isoDisplay.set('default value')

        # call a dummy dialog with an impossible option to initialize the file
        # dialog without really getting a dialog window; this will throw a TclError
        try:
            self.parent.tk.call('tk_getOpenFile', '-foobarbaz')
        except TclError:
            pass
        self.parent.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
        self.parent.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')

        self.pack(fill=BOTH, expand=1)
        self.canvas = Canvas(self)

    def selectISO(self):
        self.iso = filedialog.askopenfilename(initialdir = str(Path.home()),
                title = 'Select ISO image', 
                filetypes = (('ISO files', '*.iso'), ('all files', '*.*')))

        if str(self.iso) == '()':
            self.iso = ''

        self.isoDisplay.set(self.iso)
        print('iso = {0}'.format(self.iso))


def main():
    root = Tk()
    g = GUI(root)
    root.geometry('660x560')
    root.mainloop()

if __name__ == '__main__':
    main()
