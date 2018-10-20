#!/usr/bin/env python3
from PyQt5 import QtCore, QtGui, QtWidgets
from pathlib import Path
import sys

class GUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName('MainWindow')
        self.resize(660, 330)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName('centralwidget')

        self.instructions = QtWidgets.QLabel(self.centralwidget)
        self.instructions.setGeometry(QtCore.QRect(10, 10, 261, 71))
        self.instructions.setObjectName('instructions')

        self.browseButton = QtWidgets.QPushButton(self.centralwidget)
        self.browseButton.setGeometry(QtCore.QRect(560, 110, 89, 25))
        self.browseButton.setObjectName('browseButton')

        self.isoBox = QtWidgets.QLineEdit(self.centralwidget)
        self.isoBox.setGeometry(QtCore.QRect(10, 110, 531, 25))
        self.isoBox.setReadOnly(True)
        self.isoBox.setObjectName('isoBox')

        self.partitionsDropDown = QtWidgets.QComboBox(self.centralwidget)
        self.partitionsDropDown.setGeometry(QtCore.QRect(10, 200, 86, 25))
        self.partitionsDropDown.setObjectName('partitionsDropDown')

        self.partitionsInstructions = QtWidgets.QLabel(self.centralwidget)
        self.partitionsInstructions.setGeometry(QtCore.QRect(10, 180, 521, 17))
        self.partitionsInstructions.setObjectName('partitionsInstructions')

        self.refreshPartitionsButton = QtWidgets.QPushButton(self.centralwidget)
        self.refreshPartitionsButton.setGeometry(QtCore.QRect(180, 200, 141, 25))
        self.refreshPartitionsButton.setObjectName('refreshPartitionsButton')

        self.goButton = QtWidgets.QPushButton(self.centralwidget)
        self.goButton.setGeometry(QtCore.QRect(560, 290, 89, 25))

        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.goButton.setFont(font)
        self.goButton.setObjectName('goButton')
        self.setCentralWidget(self.centralwidget)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

        self.browseButton.clicked.connect(self.selectISO)
    
    def selectISO(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Select ISO Image', str(Path.home()), 'ISO files (*.iso);;All Files (*)', options=options)[0]

        if filename:
            print(filename)
            self.isoBox.setText(filename)
        else:
            self.isoBox.setText('click \'browse\' to select the desired ISO image')

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate('MainWindow', 'Bootable Disk Creator GUI'))
        self.instructions.setText(_translate('MainWindow', 'Here\'s how to use this application:\n'
                                             '1. Select your ISO image\n'
                                             '2. Select the partition to be used\n'
                                             '3. Click \'Go!\' and we\'ll handle the rest'))
        self.browseButton.setText(_translate('MainWindow', 'Browse'))
        self.isoBox.setText(_translate('MainWindow', 'click \'browse\' to select the desired ISO image'))
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
