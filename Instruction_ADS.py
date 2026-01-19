# -*- coding: utf-8 -*-
# Python 3

from qgis.core import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from console import *
import sys, os.path;

sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
sys.path.append(os.path.dirname(__file__)) 

# Import the code for the dialog
from Instruction_ADS import doDlgBox_IADS, doAbout_IADS

class MainPlugin(object):
      
    def __init__(self,iface):
        self.name = "Instruction_ADS"
        # Initialise et sauvegarde l'interface QGIS en cours
        self.iface = iface

    def initGui(self):
        #déclaration des actions élémentaires
        #menuIcon = resolve("Instruction_ADSico.jpg")
        menuIcon = getThemeIcon("Instruction_ADSico.jpg")
        self.commande1 = QAction(QIcon(menuIcon),"Instruction_ADS",self.iface.mainWindow())
        self.commande1.setText("Instruction_ADS")

        menuIcon1 = resolve("about.png")
        self.about = QAction(QIcon(menuIcon1), "A propos ...", self.iface.mainWindow())
        self.about.setText("A propos ...")
        
        #Connection de la commande à l'action PYQT5
        self.commande1.triggered.connect(self.LoadDlgBoxQt1)
        self.about.triggered.connect(self.doInfo)
        
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.commande1)
        self.iface.addPluginToMenu("Instruction_ADS", self.commande1)

#        # ouvre une console Qpython (pour debug et affichage commandes "print(), à désactiver pour l'utilisation)
#        maconsole = console.PythonConsole(self.iface.mainWindow())    # fenetre fixe
#        maconsole.setWindowTitle("Console RechercheCommunes6")
#        maconsole.setVisible(True)

    def unload(self): 
  
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("Instruction_ADS",self.commande1)
        self.iface.removeToolBarIcon(self.commande1)

    def LoadDlgBoxQt1(self):
        d = doDlgBox_IADS.Dialog()
        #d.show()
        d.exec_()
     
    def doInfo(self):
        d = doAbout_IADS.Dialog()
        d.exec_()
 
#Fonction de reconstruction du chemin absolu vers la ressource image
def resolve(name, basepath=None):
  if not basepath:
    basepath = os.path.dirname(os.path.realpath(__file__))
  return os.path.join(basepath, name)  
  
def getThemeIcon(theName):
    basepath = os.path.dirname(os.path.realpath(__file__))
    myDefPathIcons =basepath + "/icons/"
    myDefPathIcons = myDefPathIcons.replace("\\","/")+ theName;
    if QFile.exists(myDefPathIcons): return myDefPathIcons  
    else: return ""