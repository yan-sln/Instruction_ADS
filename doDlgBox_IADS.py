# -*- coding: utf-8 -*-
# Python 3

#from qgis.PyQt.QtCore import *
#from qgis.PyQt.QtGui import *
#from qgis.gui import QgsMessageBar
#from qgis.core import *
 	
#from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QAction
from qgis.PyQt.QtWidgets import QDialog

# Import libs
#import timeit, math, sys, os.path; sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sys, os.path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

#import de la classe boîte de dialogue "objets QWidgets"
from dlgBox_IADS import Ui_Dialog

class Dialog(QDialog,Ui_Dialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
