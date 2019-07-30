# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(607, 839)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMaximumSize(QtCore.QSize(16777215, 16777215))
        MainWindow.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        MainWindow.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralWidget)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(self.centralWidget)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_NewSubject = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_NewSubject.setObjectName("pushButton_NewSubject")
        self.horizontalLayout_2.addWidget(self.pushButton_NewSubject)
        self.pushButton_Search = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_Search.setObjectName("pushButton_Search")
        self.horizontalLayout_2.addWidget(self.pushButton_Search)
        self.lineEdit_pathSearch = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_pathSearch.setObjectName("lineEdit_pathSearch")
        self.horizontalLayout_2.addWidget(self.lineEdit_pathSearch)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralWidget)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.pushButton_Offline = QtWidgets.QPushButton(self.groupBox_2)
        self.pushButton_Offline.setObjectName("pushButton_Offline")
        self.horizontalLayout_3.addWidget(self.pushButton_Offline)
        self.pushButton_Train = QtWidgets.QPushButton(self.groupBox_2)
        self.pushButton_Train.setObjectName("pushButton_Train")
        self.horizontalLayout_3.addWidget(self.pushButton_Train)
        self.pushButton_Online = QtWidgets.QPushButton(self.groupBox_2)
        self.pushButton_Online.setObjectName("pushButton_Online")
        self.horizontalLayout_3.addWidget(self.pushButton_Online)
        self.verticalLayout_2.addWidget(self.groupBox_2)
        self.widget = QtWidgets.QWidget(self.centralWidget)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 11, 11, 11)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(self.widget)
        self.splitter.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setAutoFillBackground(False)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setChildrenCollapsible(True)
        self.splitter.setObjectName("splitter")
        self.groupBox_3 = QtWidgets.QGroupBox(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(5)
        sizePolicy.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.tabWidget_Params = QtWidgets.QTabWidget(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_Params.sizePolicy().hasHeightForWidth())
        self.tabWidget_Params.setSizePolicy(sizePolicy)
        self.tabWidget_Params.setObjectName("tabWidget_Params")
        self.BasicsParams = QtWidgets.QWidget()
        self.BasicsParams.setObjectName("BasicsParams")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.BasicsParams)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.scrollArea = QtWidgets.QScrollArea(self.BasicsParams)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents_Basics = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_Basics.setGeometry(QtCore.QRect(0, 0, 532, 393))
        self.scrollAreaWidgetContents_Basics.setObjectName("scrollAreaWidgetContents_Basics")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents_Basics)
        self.verticalLayout_3.addWidget(self.scrollArea)
        self.tabWidget_Params.addTab(self.BasicsParams, "")
        self.AdvancedParams = QtWidgets.QWidget()
        self.AdvancedParams.setObjectName("AdvancedParams")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.AdvancedParams)
        self.verticalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.scrollArea_2 = QtWidgets.QScrollArea(self.AdvancedParams)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_Adv = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_Adv.setGeometry(QtCore.QRect(0, 0, 532, 393))
        self.scrollAreaWidgetContents_Adv.setObjectName("scrollAreaWidgetContents_Adv")
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_Adv)
        self.verticalLayout_5.addWidget(self.scrollArea_2)
        self.tabWidget_Params.addTab(self.AdvancedParams, "")
        self.verticalLayout_4.addWidget(self.tabWidget_Params)
        self.groupBox_4 = QtWidgets.QGroupBox(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_6.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(10, -1, -1, -1)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.checkBox_Record = QtWidgets.QCheckBox(self.groupBox_4)
        self.checkBox_Record.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_Record.sizePolicy().hasHeightForWidth())
        self.checkBox_Record.setSizePolicy(sizePolicy)
        self.checkBox_Record.setMaximumSize(QtCore.QSize(80, 16777215))
        self.checkBox_Record.setObjectName("checkBox_Record")
        self.horizontalLayout_5.addWidget(self.checkBox_Record)
        self.pushButton_Start = QtWidgets.QPushButton(self.groupBox_4)
        self.pushButton_Start.setObjectName("pushButton_Start")
        self.horizontalLayout_5.addWidget(self.pushButton_Start)
        self.pushButton_Stop = QtWidgets.QPushButton(self.groupBox_4)
        self.pushButton_Stop.setObjectName("pushButton_Stop")
        self.horizontalLayout_5.addWidget(self.pushButton_Stop)
        self.verticalLayout_6.addLayout(self.horizontalLayout_5)
        self.textEdit_terminal = QtWidgets.QTextEdit(self.groupBox_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.textEdit_terminal.sizePolicy().hasHeightForWidth())
        self.textEdit_terminal.setSizePolicy(sizePolicy)
        self.textEdit_terminal.setMinimumSize(QtCore.QSize(0, 0))
        self.textEdit_terminal.setObjectName("textEdit_terminal")
        self.verticalLayout_6.addWidget(self.textEdit_terminal)
        self.horizontalLayout.addWidget(self.splitter)
        self.verticalLayout_2.addWidget(self.widget)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 607, 20))
        self.menuBar.setObjectName("menuBar")
        MainWindow.setMenuBar(self.menuBar)

        self.retranslateUi(MainWindow)
        self.tabWidget_Params.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox.setTitle(_translate("MainWindow", "Subject"))
        self.pushButton_NewSubject.setText(_translate("MainWindow", "New"))
        self.pushButton_Search.setText(_translate("MainWindow", "Search"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Modality"))
        self.pushButton_Offline.setText(_translate("MainWindow", "Offline"))
        self.pushButton_Train.setText(_translate("MainWindow", "Train"))
        self.pushButton_Online.setText(_translate("MainWindow", "Online"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Parameters"))
        self.tabWidget_Params.setTabText(self.tabWidget_Params.indexOf(self.BasicsParams), _translate("MainWindow", "Basics"))
        self.tabWidget_Params.setTabText(self.tabWidget_Params.indexOf(self.AdvancedParams), _translate("MainWindow", "Advanced"))
        self.groupBox_4.setTitle(_translate("MainWindow", "Launch"))
        self.checkBox_Record.setText(_translate("MainWindow", "Record"))
        self.pushButton_Start.setText(_translate("MainWindow", "Start"))
        self.pushButton_Stop.setText(_translate("MainWindow", "Stop"))


