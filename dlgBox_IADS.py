# -*- coding: utf-8 -*-
# Python 3

"""
/***************************************************************************
 Fichier des fonctions du plugin Instruction ADS

 Zoome sur l'emprise d'une parcelle cadastrale du département 
 et interroge les couches du projet relatif à l' Administration du Droit des Sols
                              -------------------
        begin                : 2023-08-09 
        deployment           : 2025-05-01 
        copyright            : (C) 2024 par Jean-Christophe Baudin DDT21/SUCAT/BGAT
                               remerciements à Francois.Thevand ,Philippe Desbouefs, Serge Torrens, Alain Ferraton pour leur aide sur la liste:
                               https://developpement-durable.listes.m2.e2.rie.gouv.fr/sympa/info/labo.qgis-python
        email                : jean-christophe.baudin@cote-dor.gouv.fr
 ***************************************************************************/

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.gui import *
from qgis.utils import iface
from qgis.core import *
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
                       )
# Import libs 
import sys, os.path; sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

from pathlib import *


import processing
from processing import *
import odswriter as ods
import fonctions_lnstruction_ADS
import doAbout_IADS

#Fonction de reconstruction du chemin absolu vers une ressource du plugin
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
    
def get_plugin_directory():
    # Obtenir le chemin du fichier courant
    current_file_path = os.path.abspath(__file__)
    # Déterminer le répertoire parent (le dossier du plugin)
    plugin_directory = os.path.dirname(current_file_path)
    return plugin_directory    

def get_plugin_version():
    # Utilisez la fonction existante pour obtenir le chemin du plugin
    plugin_dir = get_plugin_directory()
    # Chemin vers metadata.txt
    metadata_path = os.path.join(plugin_dir, "metadata.txt")
    # Lire le fichier et extraire la version
    with open(metadata_path, "r") as f:
        for line in f:
            if line.startswith("version="):
                return line.split("=")[1].strip()
    return "Unknown"
    
class Ui_Dialog(object):
    def setupUi(self,Dialog):
    
        ##############################################################################################################################################
        #                Parametrage du plugin par rapport au projet QGIS local- déclaration des variables - couches à utiliser
        ##############################################################################################################################################
        
        global project_local_path,Liste_des_couches_necessaires,nom_couche_commune, nom_couche_divcad, nom_couche_parcelle, nom_raster_scan25, nom_raster_ortho,Liste_des_groupes_a_interroger,marge_autour_parcelle,nom_projet_maitre
        
        # l'utilisateur insère ici la liste des noms des couches de sa base de données qui sont utilisées dans le projet QGIS
        
        nom_couche_commune='COMMUNE'
        nom_couche_divcad='FEUILLE'
        nom_couche_parcelle='PARCELLE'
        
        """
        nom_couche_commune='N_COMMUNE_BDP_021'  
        nom_couche_divcad='N_DIVCAD_BDP_021'
        nom_couche_parcelle='N_PARCELLE_BDP_021'
        """
        
        
        nom_raster_ortho='N_ORTHO_COUL_2017_021'
        nom_raster_scan25='n_scan25_tour_021'
        marge_autour_parcelle=600 # marge_autour_parcelle=500
        Liste_des_couches_necessaires=[nom_couche_commune, nom_couche_divcad, nom_couche_parcelle]
        
        # les données, couches à interroger sont rassemblées par thematiques dans des groupes à interroger.
        # NOTA BENE: ces groupes ne douvent pas avoir de sous groupes !
        # cela permet au projet de contenir d'autres couches dans d'autres groupes à ne pas interroger
        #Liste_des_groupes_a_interroger=['Biodiversité','Patrimoine','Eau','Nuisances','Autres SUP','Urbanisme','Gestionnaires de réseau','Nature Paysage','Specifiques projets photovoltaïques','Agriculture']
        Liste_des_groupes_a_interroger=['Eau','Autres SUP','Urbanisme','Nuisances','Risques naturels', 'Biodiversité','Patrimoine','Risques technologiques','Agriculture','Specifiques projets photovoltaïques'] 

        ##########################################################################
        #         Vérification  de la présence de la copie locale du projet
        #                 "Maitre"  et des données liées
        ##########################################################################

        # Use whatever project/layers are currently open in QGIS
        project_local_path = QgsProject.instance().fileName()
        
        ###########################################################################################
        #         Vérifications de la présence des données du projet dédié à l'ADS 
        ###########################################################################################
            
        couche_cadastre=''
        Liste_couches_verifiee=[]
        Liste_couches_manquantes=[]
        Go=True
        layermap=QgsProject.instance().mapLayers()
        for c in range(len(Liste_des_couches_necessaires)):
            absence=True
            for name,layer in layermap.items():
                couche_cadastre = Liste_des_couches_necessaires[c]
                if layer.type()== QgsMapLayer.VectorLayer and layer.name() == couche_cadastre:
                    absence=False
                    if layer.isValid():
                        Liste_couches_verifiee.append(layer.name())
        if absence: 
            Go=False
            Liste_couches_manquantes.append(couche_cadastre)
         
         
        #--------------------------------------------------------------------------------------------------------  
        #                fabrication des dictionnaires necessaires aux combobox et aux traitements
        #--------------------------------------------------------------------------------------------------------  
       
        if Go:
            #  on rend la couche nom_couche_parcelle active pour permettre une selection de parcelles directe
            couche_parcelle=fonctions_lnstruction_ADS.getVectorLayerByName(nom_couche_parcelle)
            iface.setActiveLayer(couche_parcelle)
            try:
                global Dico_Communes,Liste_Communes,Couche_Commune
                Dico_Communes={}
                Liste_Communes=[""]
                Couche_Commune=fonctions_lnstruction_ADS.getVectorLayerByName(nom_couche_commune)
                feat_commune=QgsFeature()
                # on charge les données dans un dictionnaire
                for feat_commune in Couche_Commune.getFeatures():
                    # pour recreer les tables finales on met dans attributs
                    # les valeurs des  attributs des objets de la couche de lignes
                    attributs = feat_commune.attributes()
                    # version avec 'N_COMMUNE_PCIe_021'
                    nom_commune=feat_commune['NOM_COM']
                    insee=feat_commune['CODE_INSEE']
                    Liste_Communes.append(nom_commune) 
                    Poly_id = feat_commune.id()
                    geom_commune=feat_commune.geometry()
                    XMIN=(geom_commune.boundingBox()).xMinimum()
                    YMIN=(geom_commune.boundingBox()).yMinimum()
                    XMAX=(geom_commune.boundingBox()).xMaximum()
                    YMAX=(geom_commune.boundingBox()).yMaximum()
                    Dico_Communes[feat_commune['CODE_INSEE']]=[Poly_id,nom_commune,XMIN,YMIN,XMAX,YMAX,insee]

            except: iface.messageBar().pushMessage('Pb','Attention ce projet ne convient pas ! Pb avec la couche des communes !', Qgis.Warning)
        else :
            
            QMessageBox.information(None,"information:",'Attention, ce projet ne convient pas : '+ '\n'+'en effet, il manque une ou des couches cadastrales nécessaires à cette extension: '+'\n'+'\n'+
                 '\n'+ "Pour fonctionner le projet doit contenir à minima les couches 'cadastrales' qui doivent être spécifiées lignes 71 à 80 du script dlgbox_IADS.py !"+
            '\n'+'\n'+ " On veillera à adapter aussi les lignes du code de dlgbox_IADS.py partout où les attributs de ces couches sont utilisés en précisant les noms de ceux-ci. "+
            '\n'+ '\n'+" Les couches de zonages à interroger seront rangées dans des groupes spécifiques qui doivent aussi être listés dans le corps du script juste après la définition des couches (ligne 86)!") 
            iface.messageBar().pushMessage('Plugin Instruction ADS','Attention, ce projet ne convient pas car il manque des couches nécessaires à cette extension !', Qgis.Warning)                 
            
           
        # déclaration de variables globales relatives aux parcelles cadastrales
        # pour permettre d'utiliser directement des sélections d'objets (polygones de parcelles) depuis QGIS
           
        global Dico_Parcelles,Liste_Parcelles,Couche_Parcelle
        Dico_Parcelles={}
        Liste_Parcelles=[]
        Couche_Parcelle=fonctions_lnstruction_ADS.getVectorLayerByName(nom_couche_parcelle)
                                          
                                          
        #-----------------------------------------------------------------------------------------------------------
        #                                   Fabrication de l'interface   
        #-----------------------------------------------------------------------------------------------------------
        
        Dialog.setObjectName("Dialog")
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,500,650).size()).expandedTo(Dialog.minimumSizeHint()))
        #QRect(0,0,largeur,hauteur)
        # QLabel lancer recherche
        self.label10 = QLabel(Dialog)
        self.label10.setGeometry(QtCore.QRect(15,20,450,18))
        self.label10.setObjectName("label10")
        self.label10.setText(" Sélectionner et patienter le temps que les menus se rafraîchissent !  ")
        
        #Exemple de QLabel de Commune
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,50,80,23))
        self.label.setObjectName("label")
        self.label.setText("<b>Commune </b>")

        #definition QCommune_ComboBox  
        self.Commune_ComboBox = QComboBox(Dialog)
        self.Commune_ComboBox.setGeometry(QtCore.QRect(100,50,380,23))
        self.Commune_ComboBox.setObjectName("CommuneComboBox")
        #Exemple d'alimentation de la QComboBox avec LstOPGEO
        Liste_Communes.sort()
        for i in range(len(Liste_Communes)):  self.Commune_ComboBox.addItem(Liste_Communes[i])
        
        #Exemple de QLabel de Section
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,100,80,23))
        self.label.setObjectName("label")
        self.label.setText("<u>Section</u>")
        #definition QSection_ComboBox       
        self.Section_ComboBox = QComboBox(Dialog)
        self.Section_ComboBox.setGeometry(QtCore.QRect(100,100,380,23))
        self.Section_ComboBox.setObjectName("Section_ComboBox")
        
        #Exemple de ProgressBar
        texte_base="<u>parcelles :</u>"
        self.label_progress_bar = QLabel(Dialog)
        self.label_progress_bar.setGeometry(QtCore.QRect(15,135,100,18))
        self.label_progress_bar.setObjectName("label")
        self.label_progress_bar.setText("<u>Selection des</u>")
        self.label_progress_bar_s = QLabel(Dialog)
        self.label_progress_bar_s.setGeometry(QtCore.QRect(15,150,100,18))
        self.label_progress_bar_s.setObjectName("label_progress_bar")
        self.label_progress_bar_s.setText(texte_base)
        self.label_progress_bar_2s = QLabel(Dialog)
        self.label_progress_bar_2s.setGeometry(QtCore.QRect(15,165,100,18))
        self.label_progress_bar_2s.setObjectName("label_progress_bar")
        self.label_progress_bar_2s.setText("")
        
        self.progressBar = QProgressBar(Dialog)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setMinimumSize(QtCore.QSize(380, 15))
        self.progressBar.setMaximumSize(QtCore.QSize(380, 15))
        self.progressBar.setGeometry(QtCore.QRect(100,150,380,15))
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setStyleSheet(
            """QProgressBar {border: 2px solid grey; border-radius: 5px; text-align: center;}"""
            """QProgressBar::chunk {background-color: #6C96C6; width: 20px;}"""
            )
        #Pose a minima une valeur de la barre de progression / slide contrôle
        self.progressBar.setValue(0)
        
        #Exemple de QLabel de Parcelle
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,195,80,23))
        self.label.setObjectName("label")
        self.label.setText("<i>Parcelle</i>")
        #definition QParcelle_ComboBox
        self.Parcelle_ComboBox = QComboBox(Dialog)
        self.Parcelle_ComboBox.setGeometry(QtCore.QRect(100,195,380,23))
        self.Parcelle_ComboBox.setObjectName("Parcelle_ComboBox")
        
        #Exemple de QLabel nota bene
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,240,450,23))
        self.label.setObjectName("label")
        texte_label="<b><u>Nota Bene:  </b></u>"+ "   des parcelles peuvent aussi etre choisies directement via QGIS  ! "
        self.label.setText(texte_label)
               
        #Exemple de QPushButton
        self.WorkButton = QPushButton(Dialog)
        self.WorkButton.setMinimumSize(QtCore.QSize(380, 20))
        self.WorkButton.setMaximumSize(QtCore.QSize(380, 20))        
        self.WorkButton.setGeometry(QtCore.QRect(100, 290, 380, 23))
        self.WorkButton.setObjectName("Traitement")
        self.WorkButton.setText("Interroger les données")
        
        #ProgressBar main job
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,330,100,18))
        self.label.setObjectName("label")
        self.label.setText("<b>Production du</b>")
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,350,100,18))
        self.label.setObjectName("label")
        self.label.setText("<b>rapport :</b>")
  
        self.progressBar_Rapport = QProgressBar(Dialog)
        self.progressBar_Rapport.setProperty("value", 0)
        self.progressBar_Rapport.setMinimumSize(QtCore.QSize(380, 15))
        self.progressBar_Rapport.setMaximumSize(QtCore.QSize(380, 15))
        self.progressBar_Rapport.setGeometry(QtCore.QRect(100,345,380,15))
        self.progressBar_Rapport.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar_Rapport.setTextVisible(True)
        self.progressBar_Rapport.setObjectName("progressBar2")
        self.progressBar_Rapport.setStyleSheet(
            """QProgressBar {border: 2px solid grey; border-radius: 5px; text-align: center;}"""
            """QProgressBar::chunk {background-color: #6C96C6; width: 20px;}"""
            )
            
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,385,300,18))
        self.label.setObjectName("label")
        self.label.setText("<b>Choisir un dossier d'export des résultats : </b>")
        
        self.folder_widget = QgsFileWidget(Dialog)
        # https://api.qgis.org/api/classQgsFileWidget.html#a08386cb46b9515dd50193a6de73d1db2
        self.folder_widget.setGeometry(QtCore.QRect(15,410,460,18))
        self.folder_widget.setObjectName("Chemin")
        #https://gis.stackexchange.com/questions/463676/where-in-qgis-plugin-code-should-i-set-the-qgsfilewidget-to-getdirectory
        self.folder_widget.setStorageMode(QgsFileWidget.StorageMode.GetDirectory)
        
        # label des options de production de cartes
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,445,200,25))
        self.label.setObjectName("label")
        self.label.setText("<b>Produire en plus une carte : </b>")
        
        #Exemple de  QCheckBox b0
        self.b0 = QCheckBox(Dialog)
        self.b0.setMinimumSize(QtCore.QSize(280, 25))
        self.b0.setMaximumSize(QtCore.QSize(280, 25))
        self.b0.setGeometry(QtCore.QRect(15, 475, 150,25))
        self.b0.setObjectName("b0")
        self.b0.setText("par zonage concerné")
        #self.b0.setChecked(True)  # retire la coche
       
        #Exemple de  QCheckBox b1
        self.b1 = QCheckBox(Dialog)
        self.b1.setMinimumSize(QtCore.QSize(280, 25))
        self.b1.setMaximumSize(QtCore.QSize(280, 25))
        self.b1.setGeometry(QtCore.QRect(150, 475, 150,25))
        self.b1.setObjectName("b1")
        self.b1.setText("avec Scan25")
        #self.b1.setChecked(True)  # retire la coche
        #checkBox.setChecked(True)    met la coche
        
        #Exemple de  QCheckBox b2
        self.b2 = QCheckBox(Dialog)
        self.b2.setMinimumSize(QtCore.QSize(280, 25))
        self.b2.setMaximumSize(QtCore.QSize(280, 25))
        self.b2.setGeometry(QtCore.QRect(250, 475, 150,25))
        self.b2.setObjectName("b2")
        self.b2.setText("avec Orthophotoplan")
        #self.b2.setChecked(True)  # retire la coche
        #checkBox.setChecked(True)    met la coche
        
        #Exemple de  QCheckBox b3
        self.b3 = QCheckBox(Dialog)
        self.b3.setMinimumSize(QtCore.QSize(280, 25))
        self.b3.setMaximumSize(QtCore.QSize(280, 25))
        self.b3.setGeometry(QtCore.QRect(390, 475, 150,25))
        self.b3.setObjectName("b3")
        self.b3.setText(" ''rapprochée'' ")
        #self.b3.setChecked(True)  # retire la coche
        #checkBox.setChecked(True)    met la coche
        
        #Exemple de QPushButton
        self.CloseButton = QPushButton(Dialog)
        self.CloseButton.setMinimumSize(QtCore.QSize(70, 20))
        self.CloseButton.setMaximumSize(QtCore.QSize(70, 20))        
        self.CloseButton.setGeometry(QtCore.QRect(405, 510,70, 20))
        self.CloseButton.setObjectName("CloseButton")
        self.CloseButton.setText(" Quitter !")
        
        #Exemple de QPushButton
        self.aboutButton = QPushButton(Dialog)
        self.aboutButton.setMinimumSize(QtCore.QSize(70, 20))
        self.aboutButton.setMaximumSize(QtCore.QSize(70, 20))        
        self.aboutButton.setGeometry(QtCore.QRect(15, 510, 70, 23))
        self.aboutButton.setObjectName("aboutButton")
        self.aboutButton.setText(" A propos...")
        
        #Exemple de QPushButton
        self.ExportRapports = QPushButton(Dialog)
        self.ExportRapports.setMinimumSize(QtCore.QSize(180, 20))
        self.ExportRapports.setMaximumSize(QtCore.QSize(300, 20))        
        self.ExportRapports.setGeometry(QtCore.QRect(95, 510,300, 23))
        self.ExportRapports.setObjectName("ExportRapportsButton")
        self.ExportRapports.setText(" Produire exports et cartes éventuelles !")
        
        #ProgressBar production des  cartes éventuelles
        self.label = QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(15,550,300,18))
        self.label.setObjectName("label")
        self.label.setText("<b>Production des exports et éventuelles cartes :</b>")
         
        self.progressBar_Cartes = QProgressBar(Dialog)
        self.progressBar_Cartes.setProperty("value", 0)
        self.progressBar_Cartes.setMinimumSize(QtCore.QSize(380, 15))
        self.progressBar_Cartes.setMaximumSize(QtCore.QSize(380, 15))
        self.progressBar_Cartes.setGeometry(QtCore.QRect(100,575,380,15))
        self.progressBar_Cartes.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar_Cartes.setTextVisible(True)
        self.progressBar_Cartes.setObjectName("progressBar2")
        self.progressBar_Cartes.setStyleSheet(
            """QProgressBar {border: 2px solid grey; border-radius: 5px; text-align: center;}"""
            """QProgressBar::chunk {background-color: #6C96C6; width: 20px;}"""
            )
        #Pose a minima une valeur de la barre de progression / slide contrôle
        self.progressBar.setValue(0)    
        self.progressBar_Rapport.setValue(0)
        self.progressBar_Cartes.setValue(0)
        
        #-----------------------------------------------------------------------------------------------------------
        #                                    Connexion des slots et des actions liées
        #-----------------------------------------------------------------------------------------------------------
        self.Commune_ComboBox.activated[str].connect(self.onCombo)
        self.Section_ComboBox.activated[str].connect(self.onCombo2)
        self.Parcelle_ComboBox.activated[str].connect(self.onCombo3)
        self.aboutButton.clicked.connect(self.doAbout)
        self.WorkButton.clicked.connect(self.doInterrogation)
        self.CloseButton.clicked.connect(Dialog.reject)
        self.ExportRapports.clicked.connect(self.Exports)
        self.folder_widget.fileChanged.connect(self.onCombo4)
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
         
    #-----------------------------------------------------------------------------------------------------------   
    #                                      Définitions des actions que lancent les slots   
    #-----------------------------------------------------------------------------------------------------------
 
    def retranslateUi(self, Dialog):
        version = get_plugin_version()
        Dialog.setWindowTitle(f"Instruction_ADS (v{version})")
        
    def onCombo(self):
        Selection_commune = self.Commune_ComboBox.currentText()
        if Selection_commune !=(""):
            nom = str(Selection_commune)
            self.affiche_resultat_et_zoom(nom,Dico_Communes)
        
        global Dico_Sections,Liste_Sections,Couche_Sections
        Dico_Sections={}
        Liste_Sections=[]
        Couche_Sections=fonctions_lnstruction_ADS.getVectorLayerByName(nom_couche_divcad)
        feat_section=QgsFeature()
        # on charge les données dans un dictionnaire
        for feat_section in Couche_Sections.getFeatures():
            nom_commune=feat_section['NOM_COM']
            if nom_commune == Selection_commune:
                attributs = feat_section.attributes()
                num_feuille=feat_section['FEUILLE']
                nom_section=feat_section['SECTION']
                nom_section_feuille= nom_section+'_feuille_'+str(num_feuille)
                nom_commune=feat_section['NOM_COM']
                Liste_Sections.append(nom_section_feuille) 
                Poly_id = feat_section.id()
                geom_section=feat_section.geometry()
                XMIN=(geom_section.boundingBox()).xMinimum()
                YMIN=(geom_section.boundingBox()).yMinimum()
                XMAX=(geom_section.boundingBox()).xMaximum()
                YMAX=(geom_section.boundingBox()).yMaximum()
                Dico_Sections[nom_section_feuille]=[Poly_id,num_feuille,nom_commune,nom_section,XMIN,YMIN,XMAX,YMAX]
        self.Section_ComboBox.clear()
        self.Parcelle_ComboBox.clear()
        Liste_Sections.sort()
        for i in range(len(Liste_Sections)): self.Section_ComboBox.addItem(Liste_Sections[i])

    def onCombo2(self):
        Selection_commune = self.Commune_ComboBox.currentText()
        Selection_section = self.Section_ComboBox.currentText()
        for nom_section_feuille in list(Dico_Sections.keys()): 
            if nom_section_feuille  == Selection_section: 
                Xmin=Dico_Sections[nom_section_feuille][4]
                Ymin=Dico_Sections[nom_section_feuille][5]
                Xmax=Dico_Sections[nom_section_feuille][6]
                Ymax=Dico_Sections[nom_section_feuille][7]
        self.zoom_extent(Xmin,Ymin,Xmax,Ymax)
        # -----------------------------------------------------------------------------------------------------------------
        self.Parcelle_ComboBox.clear()
        #NOTA BENE: les variables dico, liste et Couche_Parcelle ont été difinies comme variables globales en début de code
        NB_parcelles=len(Couche_Parcelle.allFeatureIds()) # necessaire pour la progress bar en pourcentage
        Selection_commune = self.Commune_ComboBox.currentText()
        Selection_section = self.Section_ComboBox.currentText()
        #----------------------- Modif ds labels de la progrsee bar ! ---------------------------------------------------
        texte_progress_bar_s= '<u>parcelles de :</u>'
        self.label_progress_bar_s.setText(texte_progress_bar_s)
        texte_progress_bar_2s= '<u> '+ str(Selection_section)+'</u>'
        self.label_progress_bar_2s.setText(texte_progress_bar_2s)
        #----------------------------------------------------------------------------------------------------------------
        counterProgess=0
        for feat_parcelle in Couche_Parcelle.getFeatures():
            counterProgess=counterProgess+1
            ref_parcelle_section_feuille=str(feat_parcelle['SECTION'])+'_feuille_'+ str(feat_parcelle['FEUILLE'])
            if feat_parcelle['NOM_COM'] == Selection_commune:
                if ref_parcelle_section_feuille == Selection_section:
                    Poly_id=feat_parcelle.id()
                    nom_commune=feat_parcelle['NOM_COM']
                    code_section=feat_parcelle['SECTION']
                    feuille=feat_parcelle['FEUILLE']
                    num_parcelle=feat_parcelle['NUMERO']
                    Liste_Parcelles.append(num_parcelle)
                    geom_parcelle=feat_parcelle.geometry()
                    # on souhaite editer des cartes permettant de voir des faits générateurs d'assiettes de 500m de diamètre
                    # on se donne pour cela un seuil de zoom à 600m
                    XMIN_600=(geom_parcelle.boundingBox()).xMinimum()-marge_autour_parcelle
                    YMIN_600=(geom_parcelle.boundingBox()).yMinimum()-marge_autour_parcelle
                    XMAX_600=(geom_parcelle.boundingBox()).xMaximum()+marge_autour_parcelle
                    YMAX_600=(geom_parcelle.boundingBox()).yMaximum()+marge_autour_parcelle
                    Dico_Parcelles[num_parcelle]=[Poly_id,nom_commune,code_section,feuille,num_parcelle,XMIN_600,YMIN_600,XMAX_600,YMAX_600]
            zPercent = int(100 * counterProgess / int(NB_parcelles))
            self.progressBar.setValue(zPercent)
        self.Parcelle_ComboBox.clear()
        Liste_Parcelles.sort()
        for p in range(len(Liste_Parcelles)): 
            self.Parcelle_ComboBox.addItem(Liste_Parcelles[p])
      
    def onCombo3(self):
        Selection_commune = self.Commune_ComboBox.currentText()
        Selection_section = self.Section_ComboBox.currentText()
        Selection_Parcelle = self.Parcelle_ComboBox.currentText()
        liste_chaine=Selection_section.split('_')
        section=liste_chaine[0]
        feuille=liste_chaine[2]
        exp = "\"NOM_COM\" ='{}' AND \"SECTION\"='{}' AND\"FEUILLE\"='{}' AND \"NUMERO\" ='{}' ".format(Selection_commune,section,feuille,Selection_Parcelle)
        if Selection_Parcelle != (""):
            Couche_Parcelle.selectByExpression(exp)
            iface.mapCanvas().setSelectionColor( QColor("red") )
            self.iface = iface
            self.iface.mapCanvas = iface.mapCanvas
            self.iface.mapCanvas().refresh()
            for num_parcelle in list(Dico_Parcelles.keys()):
                if num_parcelle==Selection_Parcelle:
                    Xmin=Dico_Parcelles[num_parcelle][5] # c'est bien XMIN-600 !
                    Ymin=Dico_Parcelles[num_parcelle][6]
                    Xmax=Dico_Parcelles[num_parcelle][7]
                    Ymax=Dico_Parcelles[num_parcelle][8]
                    self.zoom_extent_parcelle(Xmin,Ymin,Xmax,Ymax)
                    
    def onCombo4(self):
        global Selection_repertoire
        Selection_repertoire = self.folder_widget.filePath()
        
    def doInterrogation(self):
        #-----------------------------------------------------------------------------------------------------------------------
        #                           Quelles couches interroger ?         
        #                     Fabrication de la liste des couches à interroger  
        #-----------------------------------------------------------------------------------------------------------------------
        counterProgess_Work=0
        zdimR=0 # variable du nombre total de couches de zonages à interroger pour la progress bar
        Liste_couches_a_interroger=[]

        global Dico_layers_a_interroger
        # On se donne le dictionnaire Dico_layers_a_interroger, il inclue les traitements à faire issu de Dico_des_traitements_des_donnees
        Dico_layers_a_interroger={}
        # rappel: la Liste_des_groupes_a_interroger a été définie en debut de code en variable globale
        #Liste_des_groupes_a_interroger=['Biodiversité','Patrimoine''Eau','Nuisances','Autres SUP','Urbanisme','Gestionnaires de réseau','Nature Paysage','Agriculture','Nature Paysage']
        
        # Pour interroger les diffrents groupes du projets on s'interesse à l'arbre à couches
        # C'est une structure arborescente classique constituée de nœuds. 
        # Il existe actuellement deux types de nœuds : les nœuds de groupe (QgsLayerTreeGroup) 
        # et les nœuds de couche (QgsLayerTreeLayer). https://docs.qgis.org/3.10/fr/docs/pyqgis_developer_cookbook/legend.html
        root = QgsProject.instance().layerTreeRoot()
                # root est un nœud de groupe et a des enfants : 
        for nom_groupe in Liste_des_groupes_a_interroger:
            groupe=root.findGroup(nom_groupe)
            if groupe is None:
                continue
            for child in groupe.children():
                if child.layer() is None:
                    continue
                name = child.layer().name()
                vLayer = QgsProject.instance().mapLayersByName(name)[0]
                if vLayer.isValid():
                    Dico_layers_a_interroger[name] = [vLayer,nom_groupe,name]
                    Liste_couches_a_interroger.append(name)
                    zdimR+=1
   
        #-----------------------------------------------------------------------------------------------------------------------
        #                                                     THE ENGINE !             
        #-----------------------------------------------------------------------------------------------------------------------
        #
        # on va stocker dans un dictionnaire les informations des couches intersectées 
        # par l'objet polygone de la ou les  parcelles sélectionnées
        # ou des couches 'concernées' = cas de l'intersection avec le buffer-servitude d'un fait générateur
        # tel que Rapport[clef=id_parcell]=[dicos des objets des couches intersectées] 
        # ou "à proximité', option à développer éventuellement dans un second temps
        #
        global Rapport, nb_de_couches
        Rapport={}
        nb_de_couches=0 
        # nb_de_couches va servir à l'iompression pour les legendes 
        # à partir de trois couches produire a un pdf à part avec les legendes 
        
        for feat_parcelle in Couche_Parcelle.selectedFeatures():
            # On se donne le dictionnaire Dico_layers_NON_concernees, il inclue les données issues de Dico_des_traitements_des_donnees
            Dico_layers_NON_concernees={}
            Rectangle_impression=[] # pour stocker l'étendue necessaires à la composition d'une carte et au bon seuil de zoom
            Parcelle_id=feat_parcelle.id()
            nom_commune=feat_parcelle['NOM_COM']
            insee=str(feat_parcelle['CODE_DEP'])+str(feat_parcelle['CODE_COM'])
            code_section=feat_parcelle['SECTION']
            feuille=feat_parcelle['FEUILLE']
            num_parcelle=feat_parcelle['NUMERO']
            rapport_name='Rapport_de_la_parcelle_'+str(num_parcelle)+'_section_'+str(code_section)+'_feuille_'+str(feuille)+'_commune_de_'+str(nom_commune)+'_insee_'+str(insee)
            
            geom_parcelle=feat_parcelle.geometry()
            XMIN=(geom_parcelle.boundingBox()).xMinimum()
            YMIN=(geom_parcelle.boundingBox()).yMinimum()
            XMAX=(geom_parcelle.boundingBox()).xMaximum()
            YMAX=(geom_parcelle.boundingBox()).yMaximum()
            Rectangle_impression=[XMIN,YMIN,XMAX,YMAX]
            # Nota Bene, on a ajouté ce dictionnaire zone_parcelle avec comme clef, l'id de l'objet polygone car une parcelle cadastrale 
            # peut intersecter plusieurs objets/zones/polygones d'une même couche de zonages règlementaires/ d'assiettes de servitudes.
            dico_attributs_zone_parcelle={}
            Liste_des_zonages_et_assiettes_concernes=[]
            couche_a_interroger= QgsVectorLayer()
            
            for key in list(Dico_layers_a_interroger.keys()):
                counterProgess_Work=counterProgess_Work+1 
                zPercentR = int(100*counterProgess_Work / int(zdimR))
                self.progressBar_Rapport.setValue(zPercentR)
                nom_couche = str(key)
                couche_a_interroger = Dico_layers_a_interroger[key][0]
                nom_du_groupe=Dico_layers_a_interroger[key][1]
                thematique=Dico_layers_a_interroger[key][2]
                # On ne doit ajouter le nom de la couche_a_interroger qu'une fois à la liste même si plusieurs polygones intersectent
                # d'ou les tests logiques suivants:
                first_couche_concernee=True 
                # Il changera de valeur si la condition d'intersection est vérifiée
                # test_d_intersection = false car test false dés qu'on change d'objet !
                test_d_intersection = False
                ftReq = QgsFeatureRequest()
                ftReq.setFilterRect(geom_parcelle.boundingBox())
                for zone in couche_a_interroger.getFeatures(ftReq):
                    zone_geom = zone.geometry()
                    test_d_intersection_par_zone=False
                    # ------------------------------------    intersecte ou pas ? ------------------------------------
                    if geom_parcelle.intersects(zone_geom):
                        test_d_intersection = True
                        test_d_intersection_par_zone=True
                        if first_couche_concernee: 
                            first_couche_concernee=False 
                            Liste_des_zonages_et_assiettes_concernes.append(nom_couche)
                            nb_de_couches+=1
                        dico_attributs_zone={}
                        attributs_couche=[attribut for attribut in couche_a_interroger.fields()]
                        for attribut in attributs_couche:
                            nom_attribut=attribut.name()
                            valeur_attribut=zone[nom_attribut]
                            dico_attributs_zone[nom_attribut]=[valeur_attribut]
                        # ----------------------------------------------------------------------------------------------------
                        dico_attributs_zone_parcelle[zone.id()]=[key,dico_attributs_zone,nom_du_groupe,thematique]
                        
                if  test_d_intersection :
                    layer='' # on y ajoutera la couche correspondante
                    Rapport[Parcelle_id]=[nom_commune,insee,code_section,feuille,num_parcelle,Liste_des_zonages_et_assiettes_concernes,geom_parcelle,dico_attributs_zone_parcelle,Rectangle_impression,couche_a_interroger,Dico_layers_NON_concernees,rapport_name]
                   
                else :  # si pas d'intersection, pas de données récupérées, on complète le dictionnaire des données non concernées en ajoutant la couche de zonage ...
                    Dico_layers_NON_concernees[nom_couche] = [couche_a_interroger,nom_du_groupe,thematique]
            # le Dico_layers_NON_concernees a evolué et on le remplace en fin de boucle sur les zonages    
            Rapport[Parcelle_id]=[nom_commune,insee,code_section,feuille,num_parcelle,Liste_des_zonages_et_assiettes_concernes,geom_parcelle,dico_attributs_zone_parcelle,Rectangle_impression,couche_a_interroger,Dico_layers_NON_concernees,rapport_name]

        # ----------------------------------------------------------------------------------------------------
        #            Fabrication des couches rapports des parcelles sélectionnées             
        # ----------------------------------------------------------------------------------------------------
        
        # on se donne une liste des couches rapports produite pour aller rechercher les couches par leurs noms 
        # Pour créer le nom du dossier des exports pdf à venir on veut savoier quel est le nom de la commune concernée ?
        global  Liste_des_couches_de_rapports_de_parcelles,nom_commune_dossier
        Liste_des_couches_de_rapports_de_parcelles=[] 
        nom_commune_dossier=''
        first_name_commune= True # à priori une seule commune, la première est la bonne, pas la peine de parcourir tout le dictionnaire !
    
        # on crée le groupe ou mettre les couches réusltats d' après:
        # https://gis.stackexchange.com/questions/75384/adding-layer-to-group-using-pyqgis
        # https://github.com/All4Gis/QGIS-cheat-sheet/blob/master/QGIS3.md
        # https://gis.stackexchange.com/questions/198296/removing-all-layers-from-group-using-pyqgis?noredirect=1&lq=1
        # on teste si le plugin a déjà servi et donc qu'un groupe Rapports existe:
        root = QgsProject.instance().layerTreeRoot()
        groupe=root.findGroup("Rapports")
        if groupe is not None:
            root.removeChildNode(groupe)
        rapport_group = root.insertGroup(0, "Rapports")
            
        counterf=0
        for key in  Rapport.keys():
            num_parcelle= Rapport[key][4]
            feuille=Rapport[key][3]
            code_section=Rapport[key][2]
            nom_commune=Rapport[key][0]
            if first_name_commune:
                first_name_commune= False
                nom_commune_dossier=str(Rapport[key][0])
            insee= Rapport[key][1]
            # create a temporary layer
            rapport_name=Rapport[key][11]
            Liste_des_couches_de_rapports_de_parcelles.append(rapport_name)
            epsg_code='2154'
            layer_rapport=QgsVectorLayer("Polygon"+"?crs=epsg:" + str(epsg_code),rapport_name, "memory")
            QgsProject.instance().addMapLayer(layer_rapport)
            prlayer_rapport = layer_rapport.dataProvider()
            # creation de la liste des attributs de la couche rapport
            ListeChamps=[]
            ListeChamps.append(QgsField("nom_commune", QVariant.String))
            ListeChamps.append(QgsField("insee", QVariant.String))
            ListeChamps.append(QgsField("Parcelle", QVariant.String))
            ListeChamps.append(QgsField("Feuille", QVariant.String))
            ListeChamps.append(QgsField("Section", QVariant.String))
            # Dico_layers_a_interroger[nom_couche] = [vLayer,nom_groupe,thematique]
            for nom_couche_zonage in list(Dico_layers_a_interroger.keys()):
                groupe=Dico_layers_a_interroger[nom_couche_zonage][1]
                ListeChamps.append(QgsField(nom_couche_zonage+'_'+groupe, QVariant.String))
            ListeChamps.append(QgsField("nom_csv", QVariant.String))
            ListeChamps.append(QgsField("chemin", QVariant.String))
            prlayer_rapport.addAttributes(ListeChamps)
            #
            layer_rapport.startEditing()
            counterf+=1
            zPercent = int(100+(2 * counterf / int(zdimR)))
            self.progressBar_Rapport.setValue(zPercent)
            #
            newfeat = QgsFeature()
            # -----------------Remplissage des attributs--------------------
            Values=[]
            Values.append(Rapport[key][0])# nom_commune
            Values.append(Rapport[key][1])# insee         
            Values.append(Rapport[key][4])# Parcelle_id
            Values.append(Rapport[key][3]) # feuille                 
            Values.append(Rapport[key][2]) # code_section
            
            Liste_des_zonages_et_assiettes_concernes=(Rapport[key][5])
            # On renseigne l'attribut à considérer d'après la liste des couches concernées
            for nom_couche_zonage in list(Dico_layers_a_interroger.keys()):
                a_considerer='non'
                for index,nom_couche in enumerate(Liste_des_zonages_et_assiettes_concernes):
                    if nom_couche==nom_couche_zonage:
                        a_considerer='OUI'
                Values.append(a_considerer) 
            Values.append('') # nom_csv                 
            Values.append('') # chemin
           
            newfeat.setAttributes(Values)
            # ------------------ fin remplissage attributs -----------------------------
            the_geom=Rapport[key][6]
            newfeat.setGeometry(the_geom) # geom_parcelle
            prlayer_rapport.addFeatures([newfeat])
            layer_rapport.commitChanges()  
           
            # -----------------------------------------------------------------------------
            #                               fin creation couche mémoire  
            # -----------------------------------------------------------------------------
             
            # ----------------------------------------------------------------------------------------------------------------------------- 
            # on veut 'remonter' les couches rapports résultats en tête de la pile des couches
            # or pas de solution directe: il faut créer un clone de la couche le placer où on veut puis suppriomer la cocuhe initiale 
            # -----------------------------------------------------------------------------------------------------------------------------      
            # on clone la couche
            clone= layer_rapport.clone()
            #  on ajoute la couche au projet sans la "montrer": avec argument false dans le groupe Rapport, en la montrant avec True
            # https://gis.stackexchange.com/questions/290938/adding-layer-to-group-in-layers-panel-using-pyqgis
            QgsProject.instance().addMapLayer(clone, False)
            #  this is to Load it to the QgsProject (set the second parameter to False since you want to define a custom position for the layer).
            #  on ajoute le clone dans le groupe des résultats
            rapport_group.addLayer(clone)
            #
            # --- Gestion de l'analyse thematique de la couche mémoire pour qu'elle ne masque pas les couches sous-jacentes
            #
            # https://gis.stackexchange.com/questions/331408/change-vector-layer-symbology-pyqgis-3
            # https://gis.stackexchange.com/questions/324889/how-do-i-access-stroke-color-and-width-of-a-simple-marker-with-python-in-qgis
            #
            single_symbol_renderer = clone.renderer()
            symbol = single_symbol_renderer.symbol()
            #Set fill colour
            symbol.setColor(QColor.fromRgb(255,128,0))
            #Set fill style
            # adding symbol.symbolLayer(0) to identify the initial simple marker layer:
            symbol.symbolLayer(0).setBrushStyle(Qt.BrushStyle(Qt.FDiagPattern))
            #Set stroke colour and width
            symbol.symbolLayer(0).setStrokeColor(QColor(255,128,0))
            symbol.symbolLayer(0).setStrokeWidth(0.9)
            # show the change
            clone.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(clone.id())
            #--------------------------------------------------------------------------------------
            
            # on supprime les couches initiales du groupe cadastre si il existe
            group_cadastre = root.findGroup('CADASTRE')
            if group_cadastre is not None:
                group_cadastre.removeLayer(layer_rapport)
        # expand/collapse the group view
        iface.mapCanvas().refresh()    
        #Couche_Parcelle.removeSelection()
        rapport_group.setExpanded(True)
        
        
    def Exports(self):    
        # ----------------------------------------------------------------------------------------------------------------------------- 
        #                            Sauvegarde et exports des couches rapports des parcelles sélectionnées       
        # ----------------------------------------------------------------------------------------------------------------------------- 
        Selection_repertoire = self.folder_widget.filePath() 
        if len(Selection_repertoire)<1 : 
            QMessageBox.information(None,"Attention:"," Faute d'avoir sélectionné un répertoire, \n le rapport sera écrit sur votre bureau")
        counter_export=0
        root = QgsProject.instance().layerTreeRoot() 
        rapport_group=root.findGroup('Rapports')
        #date = datetime.strftime(datetime.now(), "%Y_%m_%d_%H_%M_%S") # or "%Y%m%d_%H%M%S"
        date = datetime.strftime(datetime.now(), "%Y_%m_%d")
        date_H_M=datetime.strftime(datetime.now(), "%Y_%m_%d_%Hh_%Mmin")

            
        global chemin
        chemin=''
        if len(str(Selection_repertoire))>1: 
            chemin = str(Selection_repertoire)+str('/')+nom_commune_dossier+'_Rapports_ADS_'+str(date_H_M)+'/'
            if not os.path.exists(chemin):
                os.makedirs(chemin)
        else :
            bureau = os.path.join(os.path.expanduser("~"), "desktop")   
            chemin = os.path.join(bureau, f"{nom_commune_dossier}_Rapports_ADS_{date_H_M}")
            if not os.path.exists(chemin):
                os.makedirs(chemin)
        for child in rapport_group.children(): 
            #https://gis.stackexchange.com/questions/409320/getting-layer-within-a-specific-group-using-pyqgis
            couche=child.layer() 
            rapport_name=child.name()
            layer_rapport=child.layer()
           
            # Rappel  Rapport[Parcelle_id]=[nom_commune 0,insee 1,code_section 2,feuille 3,num_parcelle 4,Liste_des_zonages_et_assiettes_concernes 5, geom_parcelle 6,
            # dico_attributs_zone_parcelle 7,Rectangle_impression 8,couche_a_interroger 9,Dico_layers_NON_concernees 10,rapport_name 11]
            # rapport_name='Rapport_de_la_parcelle_'+str(num_parcelle)+'_section_'+str(code_section)+'_feuille_'+str(feuille)+'_commune_de_'+str(nom_commune)+'_insee_'+str(insee)

            # Ci dessous code rendu silencieux, à réactiver pour créer des couches shapefile dans le dossier final
            
            # export de la couche shapefile
            shp_file = os.path.join(chemin, f"{rapport_name}_{date}.shp")
            writer = QgsVectorFileWriter.writeAsVectorFormat(couche, shp_file, 'utf-8', driverName='ESRI Shapefile')
            
            ods_file = os.path.join(chemin, f"{rapport_name}_{date}")
            writer = QgsVectorFileWriter.writeAsVectorFormat(couche, ods_file, 'utf-8', driverName='ODS')
            
            # export des tables attributaires en csv des couches rapports
            # csv_file = os.path.join(chemin, f"{rapport_name}_{date}.csv")
            # csv_writer=QgsVectorFileWriter.writeAsVectorFormat(layer_rapport,csv_file, "utf-8",QgsCoordinateReferenceSystem(),driverName='CSV',layerOptions=['CREATE_CSVT=YES'])
            # a faire trouver les arguments de la version actuelle la V3 pour forcer l'utf-8 !
            # csv_writer=QgsVectorFileWriter.writeAsVectorFormatV3(layer_rapport,csv_file, "utf-8",QgsCoordinateReferenceSystem(),driverName='CSV',layerOptions=['CREATE_CSVT=YES'])
            
            # export de csv rapports pour chaque parcelle à partir du dictionnaire avec mise en forme colonne
            #fonctions_lnstruction_ADS.enregistre_csv_par_couche(chemin,rapport_name,Rapport)
            #fonctions_lnstruction_ADS.enregistre_csv_ensemble_des_parcelles(chemin,Rapport)
            
            # export au format ods de rapports pour chaque parcelle à partir du dictionnaire avec mise en forme colonne
            #fonctions_lnstruction_ADS.enregistre_ods_par_couche(chemin,rapport_name,Rapport)
            #fonctions_lnstruction_ADS.enregistre_ods_ensemble_des_parcelles(chemin,Rapport)
                                        
        # ----------------------------------------------------------------------------------------------------------
        #                   Production du rapport final au format pdf 
        # ----------------------------------------------------------------------------------------------------------   
        #            On procède comme pour un export Cartographique sans carte
        project = QgsProject.instance()             #gets a reference to the project instance
        manager = project.layoutManager()           #gets a reference to the layout manager
        layout = QgsPrintLayout(project)            #makes a new print layout object, takes a QgsProject as argument
        #--------------------------------------------------------------------------------------------------------------------   
        #                  On s'assure qu'il n'y pas de layout en mémoire (source de messages d'erreurs bloquants)
        #---------------------------------------------------------------------------------------------------------------------  
        layouts_list = manager.printLayouts()
        for layout in layouts_list:
            manager.removeLayout(layout)
        #---------------------------------------------------------------------------- 
        # on génére le pdf de rapport comme un composeur d'impression
        #---------------------------------------------------------------------------- 
        layout, manager, layoutName = fonctions_lnstruction_ADS.Export_rapport_pdf(chemin,Rapport,Liste_des_groupes_a_interroger,project,manager)                
        manager.clear() 
        # ------------------------------------------------------------------------------------------------------------
        #                                Production d'un GEoPDF ou pdf géospatial    
        # ------------------------------------------------------------------------------------------------------------
        # https://api.qgis.org/api/3.28/structQgsLayoutExporter_1_1PdfExportSettings.html#a93ddb66c1e1f541a1bed511a41f9e396
        #
        # on va générer les inputs de la fonction qui génère le GeoPDF
        # rappel: def Exports_GeoPDF(path_name,id_carte,rapport_name,projet,manager,emprise_parcelles):
        # le chemin est déjà défini
        #
        # on devra choisir d'incorporer ou non une legende selon la variable globale nb_de_couches
        # cela se fera au niveau de la fonction fonctions_lnstruction_ADS.Exports_GeoPDF à la création du layout
        # d'après la liste de couches intersecteées avec len(liste)
      
        # on doit générer l'emprise globale des parcelles qui sera stockée dans la variable Rectangle_impression
        Liste_Xmin,liste_Ymin,Liste_Xmax,liste_Ymax=[],[],[],[]
        for key in  Rapport.keys():
            num_parcelle= Rapport[key][4]
            feuille=Rapport[key][3]
            code_section=Rapport[key][2]
            nom_commune=Rapport[key][0]
            insee= Rapport[key][1]
            
            Rectangle_impression=Rapport[key][8]
            # Rectangle_impression=[XMIN,YMIN,XMAX,YMAX]
            XMIN=Rectangle_impression[0]
            Liste_Xmin.append(XMIN)
            YMIN=Rectangle_impression[1]
            liste_Ymin.append(YMIN)
            XMAX=Rectangle_impression[2]
            Liste_Xmax.append(XMAX)
            YMAX=Rectangle_impression[3]
            liste_Ymax.append(YMAX)
        Xmin,Ymin,Xmax,Ymax=min(Liste_Xmin)-marge_autour_parcelle,min(liste_Ymin)-marge_autour_parcelle,max(Liste_Xmax)+marge_autour_parcelle,max(liste_Ymax)+marge_autour_parcelle
        Rectangle_impression=[Xmin,Ymin,Xmax,Ymax]
        self.iface = iface
        self.iface.mapCanvas = iface.mapCanvas
        self.iface.mapCanvas().refresh()
        self.zoom_extent_parcelle(Xmin,Ymin,Xmax,Ymax)
        
        # on doit générer la liste des noms de l'ensemble des parcelles et des communes 
        rapport_name='Rapport des parcelles :\n'
        counter=0
        tot=len(Liste_des_couches_de_rapports_de_parcelles)
        if tot <7: # on ne peut tolérer un titre pour plus de 6 parcelles, il couvrirait la carte !
            for idr, rap in enumerate(Liste_des_couches_de_rapports_de_parcelles):
                rap=rap.replace("Rapport_de_la_parcelle_"," - ")
                rap=rap.replace("_"," ")
                counter+=1
                tot-=1
                if counter%2==0:
                    counter=0
                    rap=rap+'\n'
                elif tot==0: pass
                else: rap=rap+', '
                rapport_name=rapport_name+rap
        else: pass # le titre est juste rapport_name
        #------------------------------------------------------------------------
        #                       Extinctions/Allumage des couches
        #------------------------------------------------------------------------     

        # L'édition de carte est liée aux couches visibles, on va donc gérér cet affichage puis utilser QgsPrintLayout(project)
        
        # Pour commencer on eteint toutes les couches des groupes de couches à interroger:
        for nom_groupe in Liste_des_groupes_a_interroger:
            groupe=root.findGroup(nom_groupe)
            if groupe is None:
                continue
            groupe.setItemVisibilityChecked(False)
            for child in groupe.children():
                child.setItemVisibilityChecked(False)
                #name = child.layer().name()
                         
        # -----------------------------------------------------------------------------------
        #  on allume toutes les couches du groupe des couches "rapport" et leur étiquettes:
        rapport_group.setItemVisibilityChecked(True)
        for child in rapport_group.children():
            child.setItemVisibilityChecked(True)
            layer_rapport=child.layer()
            iface.setActiveLayer(layer_rapport)
            # -------------------------------------------------------
            #   on affiche l'étiquette parcelle pour cette couche:
            # -------------------------------------------------------
            
            label_settings = QgsPalLayerSettings()
                      
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 12))
            text_format.setSize(12)
            background_color = QgsTextBackgroundSettings()
            background_color.setFillColor(QColor('orange'))
            background_color.setEnabled(True)
            text_format.setBackground(background_color )    
            buffer_settings = QgsTextBufferSettings()
            buffer_settings.setEnabled(True)
            buffer_settings.setSize(1)
            buffer_settings.setColor(QColor("yellow"))
            text_format.setBuffer(buffer_settings) 
            label_settings.setFormat(text_format)
            label_settings.fieldName = 'Parcelle'
            label_settings.isExpression = True
            
            label_settings.drawBackground = True
            label_settings.drawBuffer = True                               
            #label_settings.placement= QgsPalLayerSettings.OverPoint
            label_settings.placement=QgsPalLayerSettings.AroundPoint
            
            #-----------------------------------------------------------
            settings_label = QgsVectorLayerSimpleLabeling(label_settings)
            layer_rapport.setLabeling(settings_label)
            layer_rapport.setLabelsEnabled(True)
            layer_rapport.triggerRepaint()
        #---------------------------------------------------------------------------- 
        #                  On s'assure qu'il n'y pas de layout en mémoire
        #---------------------------------------------------------------------------- 
        
        fonctions_lnstruction_ADS.layout_cleaner(project)
        #---------------------------------------------------------------------------- 
        #                  On allume les couches concernées
        #---------------------------------------------------------------------------- 
        for key in  Rapport.keys():
            Liste_des_zonages_et_assiettes_concernes=(Rapport[key][5])
            for nom_groupe in Liste_des_groupes_a_interroger:
                groupe=root.findGroup(nom_groupe)
                if groupe is None:
                    continue
                for child in groupe.children():
                    child_name=child.name()
                    for idc, nom_layer in enumerate(Liste_des_zonages_et_assiettes_concernes):
                        if child_name == nom_layer:
                            groupe.setItemVisibilityChecked(True)
                            child.setItemVisibilityChecked(True)
                               
        #---------------------------------------------------------------------------- 
        #                  On allume les rasters /fonds de plans prévus
        #---------------------------------------------------------------------------- 
        groupe_FDP,scan25=fonctions_lnstruction_ADS.Gestion_visibilite_des_couches_rasters(nom_raster_scan25,'Fonds de plan') # On allume le scan25
        groupe_FDP,Orthoto=fonctions_lnstruction_ADS.Gestion_visibilite_des_couches_rasters(nom_raster_ortho,'Fonds de plan') # On allume l' Orthophotoplan
         
        #---------------------------------------------
        #     On effectue l'export du layout créé:
        # ---------------------------------------------
        
        layout,manager,layoutName,nb_items_legendes,liste_noms_couches_intersectees = fonctions_lnstruction_ADS.Exports_GeoPDF(chemin,rapport_name,project,manager,Rectangle_impression,Liste_des_zonages_et_assiettes_concernes)
                
       
        #---------------------------------------------------------------------------- 
        #                  On re nettoie les layouts en mémoire
        #---------------------------------------------------------------------------- 
        layouts_list = manager.printLayouts()
        for layout in layouts_list:
            manager.removeLayout(layout)
        #---------------------------------------------------------------------------- 
        #                  On éteint les rasters /fonds de plans 
        #---------------------------------------------------------------------------- 
        groupe_FDP,scan25=fonctions_lnstruction_ADS.Gestion_extinction_des_couches_rasters(nom_raster_scan25,'Fonds de plan') # On eteint le scan25
        groupe_FDP,Orthoto=fonctions_lnstruction_ADS.Gestion_extinction_des_couches_rasters(nom_raster_ortho,'Fonds de plan') # On eteint l' Orthophotoplan
       
        #---------------------------------------------------------------------------- 
        #                  On éteint les couches concernées
        #---------------------------------------------------------------------------- 
        for key in  Rapport.keys():
            Liste_des_zonages_et_assiettes_concernes=(Rapport[key][5])
            for nom_groupe in Liste_des_groupes_a_interroger:
                groupe=root.findGroup(nom_groupe)
                if groupe is None:
                    continue
                for child in groupe.children():
                    child_name=child.name()
                    for idc, nom_layer in enumerate(Liste_des_zonages_et_assiettes_concernes):
                        if child_name == nom_layer:
                            groupe.setItemVisibilityChecked(False)
                            child.setItemVisibilityChecked(False)
                            
        # ------------------------------------------------------------------------------------------------------------
        #                                 Gestion des exports Cartographiques  unitaires
        # ------------------------------------------------------------------------------------------------------------

        # On s'est donné le choix de produire des cartes unitaires , comprendre une par zonage avec ou sans fonds de plan
        # et éventuellement "rapprochée" sur la parcelle
        Liste_des_modalites_de_cartes_a_produire=[]
        Var0=Var1=Var2=Var3=Var4=False
        Nb_modalites_cartes=0
        # Var0 c'est pour faire ou pas des cartes unitaires par zonage
        # on vérifie quelles lignes sont selectionnees
        if self.b0.isChecked():
            Var0=True 
        if Var0 == False: 
            self.progressBar_Cartes.setValue(100)   
            
        # les autres ce sont les différentes options
        if self.b1.isChecked():
            Var1=True # faire en plus une carte avec scan25 en fond de plan
            Nb_modalites_cartes+=1
        Liste_des_modalites_de_cartes_a_produire.append(Var1)
        if self.b2.isChecked():
            Var2=True # faire en plus une carte avec Orthophotoplan en fond de plan
            Nb_modalites_cartes+=1
        Liste_des_modalites_de_cartes_a_produire.append(Var2)
        if self.b3.isChecked():
            Var3=True # faire en plus une carte de détail (seuil de zoom à l'échelle de deux fois d=max(Longueur,largeur) de la 
            Nb_modalites_cartes+=1
        Liste_des_modalites_de_cartes_a_produire.append(Var3)
        
        Var4=True #c'est la carte de base
        Nb_modalites_cartes+=1  
        Liste_des_modalites_de_cartes_a_produire.append(Var4)
        
        # ---------------------------------------------------------------------------------------------------------------------------------------------
        #     Production des exports par parcelles (Dico Rapport)  par couches de zonages présentes dans le dico_attributs_zone_parcelle          
        # ---------------------------------------------------------------------------------------------------------------------------------------------
        if Var0: 
            Dico_des_cartes_a_produire={}              
            for num_parcelle in list(Rapport.keys()):
                # Rappel  Rapport[Parcelle_id]=[nom_commune 0,insee 1,code_section 2,feuille 3,num_parcelle 4,Liste_des_zonages_et_assiettes_concernes 5, geom_parcelle 6,
                # dico_attributs_zone_parcelle 7,Rectangle_impression 8,couche_a_interroger 9,Dico_layers_NON_concernees 10,rapport_name 11]
                nom_layer_dico_Rapport=Rapport[num_parcelle][11] 
                Rectangle_impression=Rapport[num_parcelle][8]
                Liste_des_zonages_et_assiettes_concernes=Rapport[num_parcelle][5]
                dico_attributs_zone_parcelle=Rapport[num_parcelle][7]
                
                # -------------------------------------------------------------------------------------------------------------------------
                #                       Question des mêmes zonages concernés - imprimables plusieurs fois:  
                #
                #  On parcourt les couches de zonage de la liste des groupes à interroger et on compare aux zonages qui concernent la parcelle  
                #  Attention un même zonage peut avoir était retenu plusieurs fois pour plusieurs objets qui intersectent la parcelle
                #  Pour ne pas multiplier les cartes on va donc se donner une Liste_des_zonages_deja_vus et une variable logique "Pas_encore_vu"
                #  et un Dico_des_zonages_a_voir pour garder la "thematique"
                #  remarque: sans cela on aurait de surcroit des layouts de mêmes noms et donc le fameux message d'erreur: 
                #  RuntimeError: wrapped C/C++ object of type QgsPrintLayout has been deleted !   
                # -------------------------------------------------------------------------------------------------------------------------
                 
                Dico_des_zonages_a_voir={}
                Liste_des_zonages_deja_vus=['No_Name']  
                
                for id_geom in list(dico_attributs_zone_parcelle.keys()):
                    thematique=dico_attributs_zone_parcelle[id_geom][3] # on la récupère car utile pour le titre de la carte... on y indiquera la thématique
                    groupe_de_la_couche_de_zonage=dico_attributs_zone_parcelle[id_geom][2]                    
                    nom_de_la_couche_de_zonage=dico_attributs_zone_parcelle[id_geom][0]
                    Pas_encore_vu=True
                    Zonzonage=groupe_de_la_couche_de_zonage+'_'+nom_de_la_couche_de_zonage
                    for idx, zonage_deja_vu in enumerate(Liste_des_zonages_deja_vus):
                        if Zonzonage == zonage_deja_vu:
                            Pas_encore_vu=False
                        else:
                            Pas_encore_vu=True
                    if Pas_encore_vu:
                        Liste_des_zonages_deja_vus.append(Zonzonage)
                        Dico_des_zonages_a_voir[nom_de_la_couche_de_zonage]=[thematique,groupe_de_la_couche_de_zonage]
                #   on a donc un dico de zonages dédoublonnés pour la parcelle  
                               
                #------------------------------------------------------------------------
                #       Etablissement du dictionnaire des exports cartographiques
                #------------------------------------------------------------------------
                
                for nom_de_la_couche_de_zonage in list(Dico_des_zonages_a_voir.keys()): 
                    thematique=Dico_des_zonages_a_voir[nom_de_la_couche_de_zonage][0]  
                    groupe_de_la_couche_de_zonage=Dico_des_zonages_a_voir[nom_de_la_couche_de_zonage][1]  
                    carte=nom_layer_dico_Rapport+'_sur_'+nom_de_la_couche_de_zonage
                    Dico_des_cartes_a_produire[carte]=[nom_layer_dico_Rapport,thematique,groupe_de_la_couche_de_zonage,nom_de_la_couche_de_zonage,Rectangle_impression]
            zdimExport=len(Dico_des_cartes_a_produire)
            zdimExport= zdimExport*Nb_modalites_cartes
            
            if zdimExport == 0: 
                QMessageBox.information(None,"Avertissement : ", "il n'y a pas de cartes à produire car pas une parcelle n'intersecte un seul zonage !")  
            else: 
                #------------------------------------------------------------------------
                #                       Extinctions / Allumages des couches
                #------------------------------------------------------------------------     
                
                # L'édition de carte est liée aux couches visibles, on va donc gérér cet affichage puis utilser QgsPrintLayout(project)
                # Pour commencer on eteint toutes les couches des groupes de couches à interroger:
                
                for nom_groupe in Liste_des_groupes_a_interroger:
                    groupe=root.findGroup(nom_groupe)
                    if groupe is None:
                        continue
                    groupe.setItemVisibilityChecked(False)
                    for child in groupe.children():
                        child.setItemVisibilityChecked(False)
                        #name = child.layer().name()
                 
                #  on éteint toutes les couches du groupe des couches "rapport" :
                rapport_group.setItemVisibilityChecked(False)
                for child in rapport_group.children():
                    child.setItemVisibilityChecked(False)
                    
                # -----------------------------------------------------------------------------------
                # on eteint les étiquettes des parcelles de la couche parcelles cadastrales
                # rappel variable global: Couche_Parcelle=fonctions_lnstruction_ADS.getVectorLayerByName(nom_couche_parcelle)
                Couche_Parcelle.setLabelsEnabled(False)
                           
       
                #---------------------------------------------------------------------------- 
                #                  On s'assure qu'il n'y pas de layout en mémoire
                #---------------------------------------------------------------------------- 
                project = QgsProject.instance()             #gets a reference to the project instance
                manager = project.layoutManager()           #gets a reference to the layout manager
                layout = QgsPrintLayout(project)            #makes a new print layout object, takes a QgsProject as argument
                layouts_list = manager.printLayouts()
                for layout in layouts_list:
                    manager.removeLayout(layout)
                
                #------------------------------------------------------------------------
                #                 Production des exports Cartographiques
                #------------------------------------------------------------------------    
                
                #  on boucle sur les couples parcelle-zonage puis sur les modalités d'export( avec ou sans Scan2, Ortho ou mode rapproché)
                for id_carte in list(Dico_des_cartes_a_produire.keys()):         
                    rapport_name=Dico_des_cartes_a_produire[id_carte][0] 
                    thematique=Dico_des_cartes_a_produire[id_carte][1]  
                    groupe_de_la_couche_de_zonage=Dico_des_cartes_a_produire[id_carte][2]  
                    nom_de_la_couche_de_zonage=Dico_des_cartes_a_produire[id_carte][3]  
                    Rectangle_impression=Dico_des_cartes_a_produire[id_carte][4]  
                    
                    # -----------------------------------------------------------------------------------------------               
                    #          Allumage de la couche rapport de l'export et de Fonds de plans des modalités
                    # -----------------------------------------------------------------------------------------------     
                    
                    # on boucle sur les modalites d'exports avec ou sans Scan2, Ortho ou mode rapproché et on gère les allumages et zooms correspondants
                    for idx, modalite in enumerate(Liste_des_modalites_de_cartes_a_produire):
                        if idx == 0 and modalite:
                            # la couche du scan 25 a pour nom nom_raster_scan25
                            # On allume le Scan 25
                            groupe_FDP,scan25=fonctions_lnstruction_ADS.Gestion_visibilite_des_couches_rasters(nom_raster_scan25,'Fonds de plan')
                            
                        if idx == 1 and modalite:
                            # la couche de l'Orthophotoplan a pour nom nom_raster_ortho
                            # On allume l' Orthophotoplan
                            groupe_FDP,Orthoto=fonctions_lnstruction_ADS.Gestion_visibilite_des_couches_rasters(nom_raster_ortho,'Fonds de plan')
                           
                         
                        # On va rallume les couches rapports une à une, ce qui impliqe que le groupe "rapport" soit visible
                        rapport_group.setItemVisibilityChecked(True)
                     
                        # nom de la couche rapport de la parcelle qui doit correspondre à la couche allumée
                        for child_rapport in rapport_group.children():
                            rapport_name_grp=child_rapport.name()
                            layer_rapport=child_rapport.layer()
                            if rapport_name_grp == rapport_name:
                                child_rapport.setItemVisibilityChecked(True)
                                layer_rapport=child_rapport.layer()
                                iface.setActiveLayer(layer_rapport)
                                
                                # on gère les seuils de zoom selon les options
                                if idx == 2 and modalite:
                                    # c'est l'option carte rapprochée on zoom à deux fois la dimension max de la parcelle
                                    Xmin=Rectangle_impression[0]
                                    Ymin=Rectangle_impression[1]
                                    Xmax=Rectangle_impression[2]
                                    Ymax=Rectangle_impression[3]
                                    Hmax=Ymax-Ymin
                                    Lmax=Xmax-Xmin
                                    if Hmax > Lmax:
                                        Dmax=Hmax
                                    else: Dmax=Lmax
                                    # on limite cette possibilité si la Dmax , la taille de parcelle est supérieure à 500m
                                    # cela reviendrait non pas à zoomer mais à dézoomer
                                    if Dmax >500: 
                                        Xmin=Rectangle_impression[0]-marge_autour_parcelle
                                        Ymin=Rectangle_impression[1]-marge_autour_parcelle
                                        Xmax=Rectangle_impression[2]+marge_autour_parcelle
                                        Ymax=Rectangle_impression[3]+marge_autour_parcelle
                                        self.zoom_extent_parcelle(Xmin,Ymin,Xmax,Ymax)
                                        iface.mapCanvas().refresh()
                                    else: 
                                        # pour le zoom, on se donne coeff comme facteur multiplicateur de la dimension maximale de la parcelle
                                        coeff=1.4
                                        Xmin=Xmin-coeff*Dmax
                                        Ymin=Ymin-coeff*Dmax
                                        Xmax=Xmax+coeff*Dmax
                                        Ymax=Ymax+coeff*Dmax
                                        self.zoom_extent_parcelle(Xmin,Ymin,Xmax,Ymax)
                                        iface.mapCanvas().refresh()
                                else:
                                    # on zoome à 600m
                                    Xmin=Rectangle_impression[0]-marge_autour_parcelle
                                    Ymin=Rectangle_impression[1]-marge_autour_parcelle
                                    Xmax=Rectangle_impression[2]+marge_autour_parcelle
                                    Ymax=Rectangle_impression[3]+marge_autour_parcelle
                                    self.zoom_extent_parcelle(Xmin,Ymin,Xmax,Ymax)
                                    iface.mapCanvas().refresh()
                                 
                                # -------------------------------------------------------
                                #   on affiche l'étiquette parcelle pour cette couche:
                                # -------------------------------------------------------

                                label_settings = QgsPalLayerSettings()
                     
                                text_format = QgsTextFormat()
                                text_format.setFont(QFont("Arial", 12))
                                text_format.setSize(12)

                                background_color = QgsTextBackgroundSettings()
                                background_color.setFillColor(QColor('white'))
                                background_color.setEnabled(True)
                                text_format.setBackground(background_color )
                                
                                label_settings.setFormat(text_format)
                                label_settings.fieldName = 'Parcelle'
                                label_settings.isExpression = True
                                label_settings.placement=QgsPalLayerSettings.AroundPoint
                                #-----------------------------------------------------------
                                
                                
                                # ------------------------------------------------------------------------------------
                                #           Question de l'échelle quant à la visibilité de la couche Parcelle
                                # -------------------------------------------------------------------------------------
                                canvas = iface.mapCanvas()
                                if Couche_Parcelle.maximumScale() > canvas.scale() and Couche_Parcelle.minimumScale() < canvas.scale(): 
                                    pass
                                    # la couche parcelle est visible sinon non
                                else:
                                    Parcelles_label_settings = QgsPalLayerSettings()
                                    # https://gis.stackexchange.com/questions/428700/pyqgis-qgspallayersettings-vector-labels-scale-visibility
                                    # on modifie l'échelle de visibilité de la couche parcelle pour la rendre visible malgré l'échelle
                                    Parcelles_label_settings.scaleVisibility = True
                                    Parcelles_label_settings.minimumScale=canvas.scale()
                                    labels_parcelles = QgsVectorLayerSimpleLabeling(Parcelles_label_settings)
                                    Couche_Parcelle.setLabelsEnabled(True)
                                    Couche_Parcelle.setLabeling(labels_parcelles)
                                    Couche_Parcelle.triggerRepaint()
                                # -------------------------------------------------------------------------------------
                                label_settings = QgsVectorLayerSimpleLabeling(label_settings)
                                layer_rapport.setLabeling(label_settings)
                                layer_rapport.setLabelsEnabled(True)
                                layer_rapport.triggerRepaint()
                                
                            else: 
                                child_rapport.setItemVisibilityChecked(False)
                                
                        # ---------------------------------------------------------------------
                        #         Allumage du zonage de la carte à imprimer
                        # ---------------------------------------------------------------------
                        
                        groupe_zonage,couche_zonage_concernee=fonctions_lnstruction_ADS.Gestion_visibilite_des_couches_vecteurs(nom_de_la_couche_de_zonage,groupe_de_la_couche_de_zonage)
                                                        
                        # ------------------------------------------------
                        #           Création d'une mise en page
                        # ---------------------------------------------
                        project = QgsProject.instance()
                        manager = project.layoutManager()
                        # selon les modaliés d'export choisies on modifie les id_carte pour créer autant de layouts différents
                        # en effet on nomme les layouts d'après cet id_carte
                        if idx == 0 and modalite: 
                            id_carte_avec_modalite=id_carte+'_sur_Scan25'
                        elif idx == 1 and modalite:
                            id_carte_avec_modalite=id_carte+'_sur_Orthophotoplan'
                        elif idx == 2 and modalite: 
                            id_carte_avec_modalite=id_carte+'_en_vue_rapprochee'
                        else: 
                            id_carte_avec_modalite=id_carte
                        
                        # ---------------------------------------------
                        #     On effectue l'export du layout créé:
                        # ---------------------------------------------
                        
                        layout, manager, layoutName=fonctions_lnstruction_ADS.Exports_cartographiques(chemin,id_carte_avec_modalite,rapport_name,couche_zonage_concernee,thematique,project,manager,Rectangle_impression,idx,modalite)
                        
                        #---------------------------------------------------------------------------- 
                        #                  On re nettoie les layouts en mémoire
                        #---------------------------------------------------------------------------- 
                        layouts_list = manager.printLayouts()
                        for layout in layouts_list:
                            manager.removeLayout(layout)
                        
                        #----------------------------------------------------------------------------------------------------
                        #                                       Gestion de la progress Bar
                        #----------------------------------------------------------------------------------------------------
                        counter_export+=1
                        zPercent = int(100*counter_export / int(zdimExport))
                        self.progressBar_Cartes.setValue(zPercent)                         
                        
                        #----------------------------------------------------------------------------------------------------
                        #                        la fin d'un export avec une modalite on eteint le fond de plan
                        # -------------------------------------------------------------------------------------------------
                        if idx == 0 and modalite:
                            groupe_FDP.setItemVisibilityChecked(False) 
                            # on a appellé scan25 la couche du scan 25 qui a pour nom nom_raster_scan25
                            QgsProject.instance().layerTreeRoot().findLayer(scan25.id()).setItemVisibilityChecked(False)
                        if idx == 1 and modalite:
                            groupe_FDP.setItemVisibilityChecked(False) 
                            # on a appellé Orthoto la couche de l'orthophotoplan qui a pour nom nom_raster_scan25
                            QgsProject.instance().layerTreeRoot().findLayer(Orthoto.id()).setItemVisibilityChecked(False)
                        
                        #----------------------------------------------------------------------------------------------
                        #         A la fin on éteint le groupe et la couche zonage considérée si il y en a eu
                        # ---------------------------------------------------------------------------------------------     
                        #
                        if idx == 2 and modalite: pass 
                        # en effet on ne fait la carte rapprochée qu'avec le cadastre pour localister la parcelle, il n'y a pas de zonage à éteindre !
                        else: 
                            if groupe_de_la_couche_de_zonage =='': pass
                            elif len(groupe_de_la_couche_de_zonage) <2: pass
                            else:
                                groupe_zonage=root.findGroup(groupe_de_la_couche_de_zonage)
                                if groupe_zonage is not None:
                                    groupe_zonage.setItemVisibilityChecked(False)
                                QgsProject.instance().layerTreeRoot().findLayer(couche_zonage_concernee.id()).setItemVisibilityChecked(False)
                                
        QMessageBox.information(None,"Avertissement:"," Fin des traitements ! \n\nLes exports sont dans le dossier :\n" + str(chemin) )

        
    def doAbout(self):
        d = doAbout_IADS.Dialog()
        d.exec_()
        
    def affiche_resultat_et_zoom(self,name,Dico):
        for insee in list(Dico.keys()): # les codes INSEE sont les clefs du dictionnaire
            if Dico[insee][1]== name: 
                    Xmin=Dico[insee][2]
                    Ymin=Dico[insee][3]
                    Xmax=Dico[insee][4]
                    Ymax=Dico[insee][5]
        self.zoom_extent(Xmin,Ymin,Xmax,Ymax)
         
    
    def zoom_extent(self,xmin,ymin,xmax,ymax):
        xmin=int(xmin)
        ymin=int(ymin)
        xmax=int(xmax)
        ymax=int(ymax)
        #On agrandit l'emprise au cas ou (min 200m)
        if xmax-xmin<200:
            xmin = xmin - (200-(xmax-xmin))/2
            xmax = xmax + (200-(xmax-xmin))/2
        if ymax-ymin<2:
            ymin = ymin - (200-(ymax-ymin))/2
            ymax = ymax + (200-(ymax-ymin))/2
        #Creation du rectangle d'emprise :
        rec = QgsRectangle(xmin, ymin, xmax, ymax)
        self.iface = iface
        self.iface.mapCanvas = iface.mapCanvas
        self.iface.mapCanvas().setExtent(rec)
        self.iface.mapCanvas().refresh()

    def zoom_extent_parcelle(self,xmin,ymin,xmax,ymax):
        xmin=int(xmin)
        ymin=int(ymin)
        xmax=int(xmax)
        ymax=int(ymax)
        #On agrandit l'emprise au cas ou (min 100m)
        if xmax-xmin<100:
            xmin = xmin - (100-(xmax-xmin))/2
            xmax = xmax + (100-(xmax-xmin))/2
        if ymax-ymin<100:
            ymin = ymin - (100-(ymax-ymin))/2
            ymax = ymax + (100-(ymax-ymin))/2
        #Creation du rectangle d'emprise :
        rec = QgsRectangle(xmin, ymin, xmax, ymax)
        self.iface = iface
        self.iface.mapCanvas = iface.mapCanvas
        self.iface.mapCanvas().setExtent(rec)
        self.iface.mapCanvas().refresh()

    def select_layer(self,layer_name, group_name):
        # https://gis.stackexchange.com/questions/409320/getting-layer-within-a-specific-group-using-pyqgis
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(group_name)
        if group is not None:
            for child in group.children():
                if child.name() == layer_name:
                    return child.layer()
                    self.iface.setActiveLayer(child.layer())