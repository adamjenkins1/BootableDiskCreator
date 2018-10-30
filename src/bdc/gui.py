#!/usr/bin/env python3
"""Contians classes to implement multithreaded PyQt GUI for BootableDiskCreator class

File name: gui.py
Author: Adam Jenkins
Date created: 10/19/2018
Date last modified: 10/29/18
Python Version: 3.6.5
"""

import sys
from pathlib import Path
from argparse import Namespace
from time import sleep
from threading import Lock
from PyQt5 import QtCore, QtGui, QtWidgets
from bdc.bootableDiskCreator import BootableDiskCreator
from bdc.dependencyChecker import DependencyChecker

class BDCThread(QtCore.QThread):
    """subclass of QThread to call the BootableDiskCreator start method"""
    def __init__(self, bdc, selectedPartition, iso, parent=None):
        """calls parent class constructor and initializes member variables"""
        QtCore.QThread.__init__(self, parent)
        self.bdc = bdc
        self.selectedPartition = selectedPartition
        self.iso = iso
        self.running = False
        self.mutex = Lock()

    def isRunning(self):
        """returns if the thread is running or not"""
        ret = False
        self.mutex.acquire()
        ret = self.running
        self.mutex.release()
        return ret

    def getBuffer(self):
        """fetches the BootableDiskCreator's string buffer and returns it"""
        ret = ''
        self.mutex.acquire()
        ret = self.bdc.getStringBuffer()
        self.mutex.release()
        return ret

    def run(self):
        """calls BootableDiskCreator start method when thread is started"""
        self.mutex.acquire()
        if not self.running:
            self.bdc.start(Namespace(device=self.selectedPartition, image=self.iso,
                                     image_mount=None, device_mount=None, silent=True))
            self.running = True
        self.mutex.release()

        while self.isRunning():
            self.mutex.acquire()
            if self.bdc.done:
                self.running = False

            self.mutex.release()
            sleep(0.01)

class LogDialog(QtWidgets.QDialog):
    """subclass of QDialog to display log output from the BootableDiskCreator class"""
    def __init__(self):
        """calls parent class constructor and initializes member variables"""
        super().__init__()
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.textEdit = QtWidgets.QTextEdit(self)
        self.setupUI()
        self.retranslateUI()
        QtCore.QMetaObject.connectSlotsByName(self)

    def setupUI(self):
        """sets UI member variable properities"""
        self.setObjectName('Dialog')
        self.resize(582, 280)
        self.gridLayout.setObjectName('gridLayout')
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText('')
        self.textEdit.setObjectName('textEdit')
        self.textEdit.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)

    def retranslateUI(self):
        """allows Qt to translate the window title"""
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate('Dialog', 'Log Output'))

    def append(self, string):
        """adds line of text to QTextEdit member variable and moves scrollbar to bottom"""
        self.textEdit.insertPlainText(string)
        scrollBar = self.textEdit.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())

class GUI(QtWidgets.QMainWindow):
    """subclass of QMainWindow to act as main interface"""
    def __init__(self):
        """calls parent class constructor and initializes member variables"""
        super().__init__()
        self.bdc = BootableDiskCreator()
        self.bdc.verbose = False
        self.centralwidget = QtWidgets.QWidget(self)
        self.instructions = QtWidgets.QLabel(self.centralwidget)
        self.iso = 'click "browse" to select the desired ISO image'
        self.selectedPartition = ''
        self.partitions = {}
        self.browseButton = QtWidgets.QPushButton(self.centralwidget)
        self.isoBox = QtWidgets.QLineEdit(self.centralwidget)
        self.partitionsDropDown = QtWidgets.QComboBox(self.centralwidget)
        self.partitionsInstructions = QtWidgets.QLabel(self.centralwidget)
        self.refreshPartitionsButton = QtWidgets.QPushButton(self.centralwidget)
        self.goButton = QtWidgets.QPushButton(self.centralwidget)
        self.bdcThread = object()
        self.logView = LogDialog()
        self.critMessageBox = QtWidgets.QMessageBox()

        self.setupUI()
        self.retranslateUI()
        self.checkRoot()

    def validISO(self):
        """returns if the current iso is valid"""
        return self.iso != 'click "browse" to select the desired ISO image'

    def displayConfirmation(self):
        """checks if both iso and partition have been selected and displays confirmation dialogue

        If the yes button is clicked, a BDCThread instance is created and the thread is started.
        After the thread has started, the logging view is displayed.
        """
        if not self.validISO() or self.selectedPartition == '':
            self.critMessageBox.setText(('You must select an ISO image AND '
                                         'partition before continuing'))
            self.critMessageBox.exec()
            return

        confirmationText = ('Warning: this program will format {0} as FAT32 '
                            'and copy your selected ISO image onto that '
                            'partition. This means that any data on \n{0} will '
                            'be PERMANENTLY lost. '
                            'Are you sure you want to continue?'.format(self.selectedPartition))

        conf = QtWidgets.QMessageBox.question(self, 'Are you sure?', confirmationText,
                                              QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                              QtWidgets.QMessageBox.No)

        if conf == QtWidgets.QMessageBox.Yes:
            self.bdcThread = BDCThread(self.bdc, self.selectedPartition, self.iso)
            self.bdcThread.start()
            self.logView.textEdit.clear()
            self.logView.show()

            while not self.bdcThread.isRunning():
                QtCore.QCoreApplication.processEvents()
                sleep(0.05)

            while self.bdcThread.isRunning():
                logOutput = self.bdcThread.getBuffer()
                if logOutput:
                    self.logView.append(logOutput)

                QtCore.QCoreApplication.processEvents()
                sleep(0.005)

    def checkRoot(self):
        """checks if the script was executed with root privilages"""
        try:
            self.bdc.checkRoot()
        except SystemExit:
            self.critMessageBox.setText('You must run this application as root')
            self.critMessageBox.exec()
            sys.exit(1)

    def setupUI(self):
        """sets UI member variable properities"""
        self.setObjectName('MainWindow')
        self.resize(660, 330)
        self.centralwidget.setObjectName('centralwidget')

        self.instructions.setGeometry(QtCore.QRect(10, 10, 261, 71))
        self.instructions.setObjectName('instructions')

        self.browseButton.setGeometry(QtCore.QRect(560, 110, 89, 25))
        self.browseButton.setObjectName('browseButton')
        self.browseButton.clicked.connect(self.selectISO)

        self.isoBox.setGeometry(QtCore.QRect(10, 110, 531, 25))
        self.isoBox.setReadOnly(True)
        self.isoBox.setObjectName('isoBox')

        self.partitionsDropDown.setGeometry(QtCore.QRect(10, 200, 100, 25))
        self.partitionsDropDown.setObjectName('partitionsDropDown')
        self.partitionsDropDown.activated[str].connect(self.partitionsDropDownActivated)

        self.partitionsInstructions.setGeometry(QtCore.QRect(10, 180, 521, 17))
        self.partitionsInstructions.setObjectName('partitionsInstructions')

        self.refreshPartitionsButton.setGeometry(QtCore.QRect(180, 200, 141, 25))
        self.refreshPartitionsButton.setObjectName('refreshPartitionsButton')
        self.refreshPartitionsButton.clicked.connect(self.refreshPartitions)

        self.goButton.setGeometry(QtCore.QRect(560, 290, 89, 25))

        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.goButton.setFont(font)
        self.goButton.setObjectName('goButton')
        self.goButton.clicked.connect(self.displayConfirmation)

        self.critMessageBox.setIcon(QtWidgets.QMessageBox.Critical)
        self.critMessageBox.setWindowTitle('Error')

        self.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(self)

    def partitionsDropDownActivated(self, text):
        """assigns partition selected from drop down to selectedPartition"""
        self.selectedPartition = text

    def selectISO(self):
        """opens file dialog for user to select desired ISO image

        The partition drop down menu is populated if a valid file was chosen.
        """
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Select ISO Image',
                                                         str(Path.home()),
                                                         'ISO files (*.iso);;All Files (*)',
                                                         options=options)[0]

        if filename:
            self.iso = filename
        else:
            self.iso = 'click "browse" to select the desired ISO image'
            self.partitionsDropDown.clear()

        self.isoBox.setText(self.iso)
        self.refreshPartitions()

    def refreshPartitions(self):
        """populates partition drop down if a valid ISO was selected and partitions are available"""
        if not self.validISO():
            return

        self.partitions = self.getAvailablePartitions()
        choices = list(self.partitions.keys())

        self.partitionsDropDown.clear()

        if choices: # choices is not empty
            if self.selectedPartition == '':
                self.selectedPartition = choices[0]

            self.partitionsDropDown.addItems(choices)
            self.partitionsDropDown.setCurrentIndex(self.partitionsDropDown
                                                    .findText(self.selectedPartition, QtCore.Qt.MatchFixedString))
        else:
            self.selectedPartition = ''

    def getAvailablePartitions(self):
        """gets list of available partitions from BootableDiskCreator class

        Partitions on primary disk are filtered out.
        """
        partitions = self.bdc.getAvailablePartitions(False)

        primary = ''
        for key, val in partitions.items():
            if val == '/' or '/boot' in val:
                primary = key[:-1]

        if primary != '':
            partitions = {key:val for (key, val) in partitions.items() if primary not in key}

        return partitions

    def retranslateUI(self):
        """allows Qt to translate the plain text"""
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate('MainWindow', 'Bootable Disk Creator GUI'))
        self.instructions.setText(_translate('MainWindow', 'Here\'s how to use this application:\n'
                                             '1. Select your ISO image\n'
                                             '2. Select the partition to be used\n'
                                             '3. Click "Go!" and we\'ll handle the rest'))
        self.browseButton.setText(_translate('MainWindow', 'Browse'))
        self.isoBox.setText(_translate('MainWindow', ('click "browse" to select the '
                                                      'desired ISO image')))
        self.partitionsInstructions.setText(_translate('MainWindow', ('Select partition from drop '
                                                                      'down menu (you must select '
                                                                      'an ISO image first)')))
        self.refreshPartitionsButton.setText(_translate('MainWindow', 'Refresh Parititions'))
        self.goButton.setText(_translate('MainWindow', 'Go!'))
