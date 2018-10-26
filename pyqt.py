#!/usr/bin/env python3
from PyQt5 import QtCore, QtGui, QtWidgets
from pathlib import Path
from bootableDiskCreator import BootableDiskCreator
from io import StringIO
from argparse import Namespace
from time import sleep
from threading import Lock
import sys
import contextlib
import os

class BDCThread(QtCore.QThread):
    def __init__(self, bdc, selectedPartition, iso, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.bdc = bdc
        self.selectedPartition = selectedPartition
        self.iso = iso
        self.running = False
        self.mutex = Lock()

    def isRunning(self):
        ret = False
        self.mutex.acquire()
        ret = self.running
        self.mutex.release()
        return ret

    def getBuffer(self):
        ret = ''
        self.mutex.acquire()
        ret = self.bdc.getStringBuffer()
        self.mutex.release()
        return ret

    def run(self):
        self.mutex.acquire()
        if not self.running:
            self.bdc.start(Namespace(device=self.selectedPartition, image=self.iso, image_mount=None, device_mount=None))
            self.running = True
        self.mutex.release()

        while(self.isRunning()):
            self.mutex.acquire()
            if self.bdc.done:
                self.running = False

            self.mutex.release()
            sleep(0.01)

class LogDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.textEdit = QtWidgets.QTextEdit(self)
        self.setupUI()
        self.retranslateUI()
        QtCore.QMetaObject.connectSlotsByName(self)

    def setupUI(self):
        self.setObjectName('Dialog')
        self.resize(582, 280)
        self.gridLayout.setObjectName('gridLayout')
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText('')
        self.textEdit.setObjectName('textEdit')
        self.textEdit.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)

    def retranslateUI(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate('Dialog', 'Log Output'))

    def append(self, string):
        self.textEdit.insertPlainText(string)
        scrollBar = self.textEdit.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())

class GUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.bdc = BootableDiskCreator()
        self.centralwidget = QtWidgets.QWidget(self)
        self.instructions = QtWidgets.QLabel(self.centralwidget)
        self.iso = ''
        self.selectedPartition = ''
        self.partitions = {}
        self.browseButton = QtWidgets.QPushButton(self.centralwidget)
        self.isoBox = QtWidgets.QLineEdit(self.centralwidget)
        self.partitionsDropDown = QtWidgets.QComboBox(self.centralwidget)
        self.partitionsInstructions = QtWidgets.QLabel(self.centralwidget)
        self.refreshPartitionsButton = QtWidgets.QPushButton(self.centralwidget)
        self.goButton = QtWidgets.QPushButton(self.centralwidget)
        self.guiSig = QtCore.pyqtSignal(str)
        self.bdcThread = object()
        self.logView = LogDialog()

        self.setupUI()
        self.retranslateUI()
        self.checkRoot()

    def displayConfirmation(self):
        # TODO: add condition to check if partition and iso were selected
        # TODO: check drive size and iso size
        confirmationText = ('Warning: this program will format {0} as FAT32 '
                            'and copy your selected ISO image onto that '
                            'partition. This means that any data on \n{0} will '
                            'be PERMANENTLY lost. '
                            'Are you sure you want to continue?'.format(self.selectedPartition))
        
        response = QtWidgets.QMessageBox.question(self, 'Are you sure?', confirmationText, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if response == QtWidgets.QMessageBox.Yes:
            self.bdcThread = BDCThread(self.bdc, self.selectedPartition, self.iso)
            self.bdcThread.start()
            self.logView.textEdit.clear()
            self.logView.show()

            while(not self.bdcThread.isRunning()):
                QtCore.QCoreApplication.processEvents()
                sleep(0.05)

            while(self.bdcThread.isRunning()):
                logOutput = self.bdcThread.getBuffer()
                if logOutput:
                    self.logView.append(logOutput)

                QtCore.QCoreApplication.processEvents()
                sleep(0.005)

    def checkRoot(self):
        try:
            self.bdc.checkRoot()
        except SystemExit:
            mb = QtWidgets.QMessageBox()
            mb.setIcon(QtWidgets.QMessageBox.Critical)
            mb.setWindowTitle('Error')
            mb.setText('You must run this application as root')
            mb.exec()
            sys.exit(1)

    def setupUI(self):
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

        self.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(self)

    def partitionsDropDownActivated(self, text):
        self.selectedPartition = text

    def selectISO(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Select ISO Image', str(Path.home()), 'ISO files (*.iso);;All Files (*)', options=options)[0]

        if filename:
            self.iso = filename
        else:
            self.iso = 'click "browse" to select the desired ISO image'
            self.partitionsDropDown.clear()
        
        self.isoBox.setText(self.iso)
        self.refreshPartitions()

    def refreshPartitions(self):
        if self.iso == 'click "browse" to select the desired ISO image':
            return 

        self.partitions = self.getAvailablePartitions()
        choices = list(self.partitions.keys())

        self.partitionsDropDown.clear()
        if len(choices) > 0:
            if self.selectedPartition == '':
                self.selectedPartition = choices[0]

            self.partitionsDropDown.addItems(choices)
            self.partitionsDropDown.setCurrentIndex(self.partitionsDropDown.findText(self.selectedPartition, QtCore.Qt.MatchFixedString))
        else:
            self.selectedPartition = ''

    def getAvailablePartitions(self):
        with contextlib.redirect_stdout(StringIO()):
            partitions = self.bdc.getAvailablePartitions(False)

        primary = ''
        for key, val in partitions.items():
            if val == '/' or '/boot' in val:
                primary = key[:-1]

        if primary != '':
            partitions = {key:val for (key, val) in partitions.items() if primary not in key}

        return partitions

    def retranslateUI(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate('MainWindow', 'Bootable Disk Creator GUI'))
        self.instructions.setText(_translate('MainWindow', 'Here\'s how to use this application:\n'
                                             '1. Select your ISO image\n'
                                             '2. Select the partition to be used\n'
                                             '3. Click "Go!" and we\'ll handle the rest'))
        self.browseButton.setText(_translate('MainWindow', 'Browse'))
        self.isoBox.setText(_translate('MainWindow', 'click "browse" to select the desired ISO image'))
        self.partitionsInstructions.setText(_translate('MainWindow', 'Select partition from drop down menu (you must select an ISO image first)'))
        self.refreshPartitionsButton.setText(_translate('MainWindow', 'Refresh Parititions'))
        self.goButton.setText(_translate('MainWindow', 'Go!'))

def main():
    app = QtWidgets.QApplication([])
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
