# -*- coding: utf-8 -*-
# Python 3

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import *
from PyQt5 import QtCore
from qgis.PyQt.QtWidgets import QGridLayout, QLabel, QTextEdit, QPushButton, QSpacerItem, QSizePolicy, QApplication,QMessageBox

# Import libs 
import sys, os.path; sys.path.append(os.path.dirname(os.path.abspath(__file__)))
 
#Fonction de reconstruction du chemin absolu vers la ressource image
def resolve(name, basepath = None):
  if not basepath:
    basepath = os.path.dirname(os.path.realpath(__file__))
  return os.path.join(basepath, name)  

def getThemeIcon(theName):
    basepath = os.path.dirname(os.path.realpath(__file__))
    myDefPathIcons =basepath + "/icons/"
    myDefPathIcons = myDefPathIcons.replace("\\","/")+ theName;
    if QFile.exists(myDefPathIcons): return myDefPathIcons  
    else: return ""
    
class Ui_Dialog(object):

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,350,400).size()).expandedTo(Dialog.minimumSizeHint()))

        self.gridlayout = QGridLayout(Dialog)
        self.gridlayout.setObjectName("gridlayout")

        self.label_2 = QLabel(Dialog)
        self.labelImage = QLabel(Dialog)

        carIcon = QImage(getThemeIcon("Instruction_ADSico.jpg"))
        self.labelImage.setPixmap(QPixmap.fromImage(carIcon))

        font = QFont()
        font.setPointSize(15) 
        font.setWeight(50) 
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setTextFormat(QtCore.Qt.RichText)
        self.label_2.setObjectName("label_2")
        self.gridlayout.addWidget(self.label_2,1,1,1,2)
        self.gridlayout.addWidget(self.labelImage,1,5,1,2)

        self.textEdit = QTextEdit(Dialog)

        palette = QPalette()

        brush = QBrush(QColor(0,0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QPalette.Active,QPalette.Base,brush)

        brush = QBrush(QColor(0,0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QPalette.Inactive,QPalette.Base,brush)

        brush = QBrush(QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled,QPalette.Base,brush)
        self.textEdit.setPalette(palette)
        self.textEdit.setAutoFillBackground(True)
        self.textEdit.width = 380
        self.textEdit.height = 380
        #self.textEdit.setFrameShape(QFrame.NoFrame)
        #self.textEdit.setFrameShadow(QFrame.Plain)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
       
        self.gridlayout.addWidget(self.textEdit,1,1,5,2) 

        self.pushButton = QPushButton(Dialog)
        self.pushButton.setObjectName("pushButton")
        self.gridlayout.addWidget(self.pushButton,4,2,1,1) 

        spacerItem = QSpacerItem(20,40,QSizePolicy.Minimum,QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem,3,5,1,1)

        self.retranslateUi(Dialog)
        self.pushButton.clicked.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QApplication.translate("Dialog", "Instruction  ADS", None))
        self.label_2.setText(QApplication.translate("Dialog", "Instruction  ADS V0", None))
        self.textEdit.setHtml(QApplication.translate("Dialog", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Sans Serif\'; font-size:8pt; font-weight:300; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'MS Shell Dlg 2\'; font-size:8pt;\"><span style=\" font-weight:600;\">"
        "Instruction ADS :</span>" "  Ce plugin est conçu pour les agents du Chargée de mission Planification Ecologique Service Economie Agricole et Environnement des Exploitations de la DDT du  souhaitant disposer dans Qgis_3 "+
        " d'une fonctionnalité permettant, à partir d'une parcelle cadastrale localisée donnée,"+
        " d'extraire de l'ensemble des couches contenues dans le projet QGIS"+
        " (comme: couches des servitudes,natrura 2000, des aléas,..etc..),celles de ces couches qui intersectent la parcelle choisie."+
        " Pour la ou les parcelle(s) choisie(s) le plugin produit une rapport pdf avec la liste des couches concernées, ainsi qu'un geopdf avec des 'vues' des couches concernées"+
        "                                                                                                                                                                               "+
       
        " Pour fonctionner le projet doit contenir à minima les couches 'cadastrales' qui doivent être spécifiées lignes 71 à 80 du script dlgbox_IADS.py !                                                                                                                                    "+
        " On veillera à adapter aussi les lignes du code de dlgbox_IADS.py partout où les attributs de ces couches sont utilisés en précisant les noms de ceux-ci                                                                                                                                                                                             "+
        " Les couches de zonages à interroger sont rangées dans des groupes spécifiques qui doivent aussi être listés dans le corps du script juste après la définition des couches!                                                                                                                                                                             "+
        " "+
        " Ces couches sont recopiées depuis le serveur sur le poste de l'agent lors de la première utilisation de l'outil et le projet 'Maître' est dupliqué en projet local.                                                                                                                  "+
        " Plusieurs fichiers.csv sont aussi créés qui témoignent des dates de copies et de créations des données: liste des couches du projet et projet lui-même."+
        " Lors des utilisations suivantes, ces rapports sont consultés pour vérifier si une couche a été modifiée sur le serveur.                                                                                   "+
        " Le cas échéant elle est mise à jour dans le projet local. "+
        " Le projet local est aussi comparé au projet Maître; toute mofication du projet Mâitre retentie sur le projet local qui est modifié en conséquence."+
        " Si l'outil a déjà été utilisé lors d'une même journée, on saute l'étape de mise à jour.                                                                                                                   "+
        " Si le projet local est ouvert car on aura lancé le plugin une première fois avant de refermer la fenêtre, on peut alors travailler sur plusieurs parcelles à la fois du moment qu'on les aura sélectionnées."+
        
        " Cette extension ne fait pas partie du moteur de Qgis. Toute demande est à adresser à l'auteur : </p></td></tr></table>"
        "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p>\n"
        "<p style=\"margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">"
        #"<font color='#0000FF'><b><u> Jean-Christophe Baudin</u></b></font><br><br>"
        "<b>ddt-mpit-adl@cote-dor.gouv.fr</b><br><b>DDT21 SUCAT/BGAT</b><br>"
        "<br><i>Version  1.1.0  (14 janvier 2026).</i></p></body></html>", None))
        self.pushButton.setText(QApplication.translate("Dialog", "OK", None))

