# -*- coding: utf-8 -*-
# Python 3

from qgis.PyQt.QtWidgets import QDialog

# Import libs 
import sys, os.path; sys.path.append(os.path.dirname(os.path.abspath(__file__)))

#import de la classe boîte de dialogue "A propos ..."
from about_IADS import Ui_Dialog

class Dialog(QDialog, Ui_Dialog):
	def __init__(self):
		QDialog.__init__(self)
		self.setupUi(self)
		
