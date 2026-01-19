
# -*- coding: utf-8 -*-
# Python 3

"""
/***************************************************************************
 Fichier des fonctions du plugin Instruction ADS

 Zoome sur l'emprise d'une parcelle cadastrale du département 
 et interroge les couches du projet relatif à l' Administration du Droit des Sols
                              -------------------
        begin                : 2023-08-09 
        deployment           : 2024-03-26 
        copyright            : (C) 2024 par Jean-Christophe Baudin DDT21/SUCAT/BGAT
                               remerciements à Francois.Thevand ,Philippe Desbouefs, Serge Torrens, Alain Ferraton pour leur aide sur la liste:
                               https://developpement-durable.listes.m2.e2.rie.gouv.fr/sympa/info/labo.qgis-python
        email                : jean-christophe.baudin@cote-dor.gouv.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import csv
import re
import os
import unicodedata,sys
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtWidgets import (QMessageBox)

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.gui import *
from qgis.utils import iface
from qgis.core import *
from qgis.core import  (QgsProject,
                        QgsMapLayer,
                        QgsVectorLayer
                       )
from datetime import datetime
import odswriter as ods

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
  
        
def getVectorLayerByName(NomCouche):
    layermap=QgsProject.instance().mapLayers()
    for name,layer in layermap.items():
        if layer.type()==QgsMapLayer.VectorLayer and layer.name()== NomCouche:
            if layer.isValid():
               return layer
            else:
               return None

def cherche_section(section, dico):
    liste = []
    liste.append("")
    for k in list(dico.keys()):
        if dico[k][2] != (str(message)):
            del dico[k]
    for c in list(dico.keys()):
        liste.append(str(c))
    liste.sort()     
    return liste, dico
    
def cherche_parcelle(commune, section, dico):
    liste2 = []
    liste2.append("")
    Dico_resultat
    # on dézingue les mauvaises communes
    for parcelle in list(dico.keys()):
        if dico[parcelle][1] == (str(commune)):
            if dico[parcelle][2] != (str(section)):
                Dico_resultat[parcelle]=dico[parcelle]
            
    for cc in list(Dico_resultat.keys()):
        liste2.append(str(cc))
    liste2.sort()  
    return liste2, Dico_resultat



def enregistre_csv_par_couche(path_name,nom_de_la_couche_rapport,DicoR):
    date_H_M=datetime.strftime(datetime.now(), "%Y_%m_%d_%Hh_%Mmin")
    csv_file_rapport= str(path_name)+'_'+str(nom_de_la_couche_rapport)+'_rapport_interrogation_'+str(date_H_M)+'.csv'
    uri_csv_file_rapport =csv_file_rapport.replace("\\","/")
    fname =  csv_file_rapport 
    fichier = open(fname, 'w',newline="")
     
    try:
        # Création de l'''écrivain'' CSV.
        spamwriter = csv.writer(fichier,delimiter=';')
        # Écriture de la ligne d'en-tête avec le titre des colonnes.
        titres=['Num_Parcelle', 'code_section','feuille','nom_commune', 'insee','Groupe-Thématique','Thématique','Donnée','Concernée','id_zonage']
        # print(titres)
        spamwriter.writerow(titres)
        
        # Écriture des  données.
        for key in sorted(DicoR.keys()):
            Parcelle_id=str(key)
            nom_commune=str(DicoR[key][0])
            insee=str(DicoR[key][1])
            code_section=str(DicoR[key][2])
            feuille=str(DicoR[key][3])
            num_parcelle=str(DicoR[key][4])
            Liste_des_zonages_et_assiettes_concernes=DicoR[key][8]
            Dico_layers_NON_concernees=(DicoR[key][10])
            dico_attributs_zone_parcelle=(DicoR[key][7])
            rapport_name=(DicoR[key][11])
            if nom_de_la_couche_rapport==rapport_name:
                for key_zone in list(dico_attributs_zone_parcelle.keys()):
                    id_zonage=str(key_zone)
                    Concernee='OUI'
                    Couche_Donnee=str(dico_attributs_zone_parcelle[key_zone][0])
                    Grpt_Thema=dico_attributs_zone_parcelle[key_zone][2]
                    Thematique=dico_attributs_zone_parcelle[key_zone][3]
                    enregistrement=[num_parcelle,code_section,feuille,nom_commune,insee,Grpt_Thema,Thematique,Couche_Donnee,Concernee,id_zonage]
                    spamwriter.writerow(enregistrement)
                
                for key_zone_NC in list(Dico_layers_NON_concernees.keys()):
                    id_zonage='Sans objet'
                    Concernee='non'
                    Couche_Donnee=key_zone_NC
                    Grpt_Thema=Dico_layers_NON_concernees[key_zone_NC][1]
                    Thematique=Dico_layers_NON_concernees[key_zone_NC][2]
                    enregistrement=[num_parcelle,code_section,feuille,nom_commune,insee,Grpt_Thema,Thematique,Couche_Donnee,Concernee,id_zonage]
                    spamwriter.writerow(enregistrement)
    finally:
        # Fermeture du fichier source
        fichier.close()


def enregistre_ods_par_couche(path_name,nom_de_la_couche_rapport,DicoR): # Save tables in OpenDocument format using odswriter library
    date_H_M=datetime.strftime(datetime.now(), "%Y_%m_%d_%Hh_%Mmin")
    ods_file_rapport= str(path_name)+'_'+str(nom_de_la_couche_rapport)+'_rapport_interrogation_'+str(date_H_M)+'.ods'
    ods_csv_file_rapport =ods_file_rapport.replace("\\","/")
    titres=['Num_Parcelle', 'code_section','feuille', 'insee','nom_commune', 'Groupe-Thématique','Thématique','Nom Couche sig','Concernée','id_zonage']
    file = ods_csv_file_rapport
    with ods.writer(open(file, "wb")) as odsfile:
        nom_ods=str(nom_de_la_couche_rapport)+'_rapport_interrogation_'+str(date_H_M)+'.ods'
        sheet = odsfile.new_sheet(nom_ods)  # For each tab in the container, a new sheet is created
        sheet.writerow(titres)
        for key in sorted(DicoR.keys()):
            Parcelle_id=str(key)
            nom_commune=str(DicoR[key][0])
            insee=str(DicoR[key][1])
            code_section=str(DicoR[key][2])
            feuille=str(DicoR[key][3])
            num_parcelle=str(DicoR[key][4])
            Liste_des_zonages_et_assiettes_concernes=DicoR[key][5]
            Dico_layers_NON_concernees=(DicoR[key][10])
            dico_attributs_zone_parcelle=(DicoR[key][7])
            rapport_name=(DicoR[key][11])
            if nom_de_la_couche_rapport==rapport_name:
                for key_zone in list(dico_attributs_zone_parcelle.keys()):
                    id_zonage=str(key_zone)
                    Concernee='OUI'
                    Couche_Donnee=str(dico_attributs_zone_parcelle[key_zone][0])
                    Grpt_Thema=dico_attributs_zone_parcelle[key_zone][2]
                    Thematique=dico_attributs_zone_parcelle[key_zone][3]
                    enregistrement=[num_parcelle,code_section,feuille,nom_commune,insee,Grpt_Thema,Thematique,Couche_Donnee,Concernee,id_zonage]
                    sheet.writerow(enregistrement)
    valsortie = True
    return valsortie
       

def enregistre_csv_ensemble_des_parcelles(path_name,DicoR):
    date_H_M=datetime.strftime(datetime.now(), "%Y_%m_%d_%Hh_%Mmin")
    csv_file_rapport= str(path_name)+'Rapport_interrogation_ADS_'+str(date_H_M)+'.csv'
    uri_csv_file_rapport =csv_file_rapport.replace("\\","/")
    fname =  csv_file_rapport 
    fichier = open(fname, 'w',newline="")
     
    try:
        # Création de l'''écrivain'' CSV.
        spamwriter = csv.writer(fichier,delimiter=';')
        titres=['Num_Parcelle', 'code_section','feuille', 'insee','nom_commune','Groupe-Thématique','Thématique','Donnée','Concernée','id_zonage']
        spamwriter.writerow(titres)
        
        # Écriture des  données.
        for key in sorted(DicoR.keys()):
            Parcelle_id=str(key)
            nom_commune=str(DicoR[key][0])
            insee=str(DicoR[key][1])
            code_section=str(DicoR[key][2])
            feuille=str(DicoR[key][3])
            num_parcelle=str(DicoR[key][4])
            Liste_des_zonages_et_assiettes_concernes=DicoR[key][8]
            Dico_layers_NON_concernees=(DicoR[key][10])
            dico_attributs_zone_parcelle=(DicoR[key][7])
            rapport_name=(DicoR[key][11])
            
            for key_zone in list(dico_attributs_zone_parcelle.keys()):
                id_zonage=str(key_zone)
                Concernee='OUI'
                Couche_Donnee=str(dico_attributs_zone_parcelle[key_zone][0])
                Grpt_Thema=dico_attributs_zone_parcelle[key_zone][2]
                Thematique=dico_attributs_zone_parcelle[key_zone][3]
                enregistrement=[num_parcelle,code_section,feuille,nom_commune,insee,Grpt_Thema,Thematique,Couche_Donnee,Concernee,id_zonage]
                spamwriter.writerow(enregistrement)
            
            for key_zone_NC in list(Dico_layers_NON_concernees.keys()):
                id_zonage='Sans objet'
                Concernee='non'
                Couche_Donnee=key_zone_NC
                Grpt_Thema=Dico_layers_NON_concernees[key_zone_NC][1]
                Thematique=Dico_layers_NON_concernees[key_zone_NC][2]
                enregistrement=[num_parcelle,code_section,feuille,nom_commune,insee,Grpt_Thema,Thematique,Couche_Donnee,Concernee,id_zonage]
                spamwriter.writerow(enregistrement)
    finally:
        # Fermeture du fichier source
        fichier.close()


def enregistre_ods_ensemble_des_parcelles(path_name,DicoR):
    date_H_M=datetime.strftime(datetime.now(), "%Y_%m_%d_%Hh_%Mmin")
    ods_file_rapport= str(path_name)+'Rapport_interrogation_ADS_'+str(date_H_M)+'.ods'
    uri_ods_file_rapport =ods_file_rapport.replace("\\","/")
    titres=['Num_Parcelle', 'code_section','feuille','nom_commune', 'insee', 'Groupe-Thématique','Thématique','couche_sig','parcelle_concernée','id_zonage']
    with ods.writer(open(uri_ods_file_rapport, "wb")) as odsfile:
        sheet = odsfile.new_sheet(uri_ods_file_rapport) 
        sheet.writerow(titres)

        for key in sorted(DicoR.keys()):
            Parcelle_id=str(key)
            nom_commune=str(DicoR[key][0])
            insee=str(DicoR[key][1])
            code_section=str(DicoR[key][2])
            feuille=str(DicoR[key][3])
            num_parcelle=str(DicoR[key][4])
            Liste_des_zonages_et_assiettes_concernes=DicoR[key][5]
            Dico_layers_NON_concernees=(DicoR[key][10])
            dico_attributs_zone_parcelle=(DicoR[key][7])
            rapport_name=(DicoR[key][11])
             
            for key_zone in list(dico_attributs_zone_parcelle.keys()):
                id_zonage=str(key_zone)
                Concernee='OUI'
                Couche_Donnee=str(dico_attributs_zone_parcelle[key_zone][0])
                Grpt_Thema=dico_attributs_zone_parcelle[key_zone][2]
                Thematique=dico_attributs_zone_parcelle[key_zone][3]
                enregistrement=[num_parcelle,code_section,feuille,nom_commune,insee,Grpt_Thema,Thematique,Couche_Donnee,Concernee,id_zonage]
                sheet.writerow(enregistrement)

    valsortie = True
    return valsortie


def Exports_cartographiques(path_name,id_carte,rapport_name,layer_du_zonage,nom_de_la_sup,projet,manager,rec_emprise_parcelle,id_liste_modalite,modalite_fond_de_carte):
    couche_zonage_concernee=layer_du_zonage
    thematique=nom_de_la_sup
    chemin=path_name.replace("\\","/")
    project=projet
    # rappel des modalite_fond_de_carte fct de leur id: 0 = Scan 25, 1= Orthophoto, 2 = rapprochée
    # ------------------------------------------------
              # Création d'une mise en page
    # ------------------------------------------------
     
    # Attention! Il faut nommer chaque mise en page / layout avec un nom différent,
    # sans quoi on a une message d'erreur "RuntimeError: wrapped C/C++ object of type QgsPrintLayout has been deleted "
    # voir https://gis.stackexchange.com/questions/436047/runtimeerror-wrapped-c-c-object-of-type-qgsprintlayout-has-been-deleted
    # on nommera les layout d'après le nom de la couche  layoutName = str(couche)
    # ou mieux : on détruit le layout une fois utiliser !
    # https://library.virginia.edu/data/articles//how-to-create-and-export-print-layouts-in-python-for-qgis-3 
    
    # project = QgsProject.instance()             #gets a reference to the project instance
    # manager = project.layoutManager()           #gets a reference to the layout manager
    layoutName = str(id_carte)
    # on doit vérifier et éventuellement dézingier tous les derniers layout pour se prémunir des erreurs si un layout.name() existe déjà !
    # https://gis.stackexchange.com/questions/436047/runtimeerror-wrapped-c-c-object-of-type-qgsprintlayout-has-been-deleted
    # https://library.virginia.edu/data/articles//how-to-create-and-export-print-layouts-in-python-for-qgis-3 
    # https://gis.stackexchange.com/questions/311390/pyqgis-managing-print-layouts
    layouts_list = manager.printLayouts()
    liste_layout_names=[]
    
    for idx, lay in enumerate(layouts_list):
        liste_layout_names.append(lay.name())

    for layout in layouts_list:
        if layout.name() == layoutName:
            manager.removeLayout(layout)
           
    liste_layout_names=[]       
    for idx, lay in enumerate(layouts_list):
        liste_layout_names.append(lay.name())        

    layout = QgsPrintLayout(project)            #makes a new print layout object, takes a QgsProject as argument
    layout.initializeDefaults()  #create default map canvas
    layout.setName(layoutName)
     # on ajoute un layout ayant nom de la couche
    manager.addLayout(layout)
    
    # la feuille A4 paysage mesure 297mm en largeur et 210mm en hauteur   
    page = QgsLayoutItemPage(layout)
    page.setPageSize('A4',  QgsLayoutItemPage.Landscape)
    page_center = page.pageSize().width() / 2
    
    # Composeur d'impression: 
    # Tous les éléments de la mise page comme carte, étiquette, 
    # …sont des objets représentés par des classes qui héritent de la classe de base QgsLayoutItem.
    # Carte:
    # This adds a map item to the Print Layout 
    map = QgsLayoutItemMap(layout)
    map.setRect(20, 20, 20, 20)  
    canvas = iface.mapCanvas()
    Etendu_du_Canvas=canvas.extent()
    # Set Extent
    if id_liste_modalite==2 and modalite_fond_de_carte:
        # sets map extent to current map canvas : on a justement zoomer sur la parcelle avec 600m autour à 300 mètres
        # ou sinon on a déjà zoomer à la bonne extent
        map.setExtent(Etendu_du_Canvas) 

    else :
        Xmin=rec_emprise_parcelle[0]
        Ymin=rec_emprise_parcelle[1]
        Xmax=rec_emprise_parcelle[2]
        Ymax=rec_emprise_parcelle[3]
        rectangle = QgsRectangle(Xmin,Ymin,Xmax,Ymax)  #an example of how to set map extent with coordinates
        map.setExtent(rectangle)
                
    # Move: les arguments sont:
    # la distance à partir du bord gauche du layout, 
    # puis la distance à partir du bord haut.
    map.attemptMove(QgsLayoutPoint(5, 26, QgsUnitTypes.LayoutMillimeters))
    # Resize :  QgsLayoutSize(largeur, hauteur , unités employées)
    map.attemptResize(QgsLayoutSize(240, 180, QgsUnitTypes.LayoutMillimeters))
    # a4 = QPageSize().size(QPageSize.A4, QPageSize.Millimeter)
    # map.attemptResize(QgsLayoutSize(a4.height(),  a4.width()))
    map.zoomToExtent(iface.mapCanvas().extent())
    layout.addLayoutItem(map)
     
    # Titre de la carte
    # This adds labels to the map
    nom=rapport_name.replace("_"," ")
    nom=nom.replace("commune","- Commune")
    nom_de_la_carte=nom+'\n'+thematique
    title = QgsLayoutItemLabel(layout)
    title.setText(nom_de_la_carte)
    title.setFont(QFont("Arial",16))
    y=7
    x=15
    layout.addLayoutItem(title)
    title.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
    title.adjustSizeToText()
    y += title.boundingRect().height()
    title.attemptResize(QgsLayoutSize(x+title.boundingRect().width(),y))
    layout.addLayoutItem(title)

    # Echelle graphique
    # on prépare la taille de la sclebar avec Etendu_du_Canvas qui est un QgsRectangle
    # https://qgis.org/pyqgis/3.2/core/other/QgsRectangle.html 
    scaleBar = QgsLayoutItemScaleBar(layout)
    scaleBar.applyDefaultSettings()
    scaleBar.setLinkedMap(map)
    scaleBar.setStyle('Single Box')    # setStyle: 'Single Box', 'Double Box', 'Line Ticks Middle', 'Line Ticks Down', 'Line Ticks Up', 'Numeric'
    scaleBar.setNumberOfSegmentsLeft(0)
    scaleBar.setNumberOfSegments(2)
    # on choisir d'avoir toujours deux segments dans l'échelle quelle doit etre la taille d'un segment ?
    H_Canvas=Etendu_du_Canvas.height()
    L_Canvas=Etendu_du_Canvas.width()
    if H_Canvas > L_Canvas: 
        Dmax_Canvas=H_Canvas
    else:
        Dmax_Canvas=L_Canvas
    # on va se donner comme taille de la barre d'échelle 1/5 de la taille maximale de l'étendue du Canevas de la carte
    scaleBar_total_size=int(Dmax_Canvas/5)
    scaleBar.setMapUnitsPerScaleBarUnit(1)  # Sets the number of map units per scale bar unit used by the scalebar:
    if scaleBar_total_size <= 100:
        scaleBar.setUnits(QgsUnitTypes.DistanceMeters)
        scaleBar.setUnitLabel("m")
        scaleBar.setUnitsPerSegment(25)
    elif scaleBar_total_size <= 500:
        scaleBar.setUnits(QgsUnitTypes.DistanceMeters)
        scaleBar.setUnitLabel("m")
        scaleBar.setUnitsPerSegment(100)
    elif scaleBar_total_size <=  1000:
        scaleBar.setUnits(QgsUnitTypes.DistanceMeters)
        scaleBar.setUnitLabel("m")
        scaleBar.setUnitsPerSegment(250)
    elif scaleBar_total_size <=  10000:
        scaleBar.setUnits(QgsUnitTypes.DistanceKilometers)
        scaleBar.setUnitLabel("km")
        scaleBar.setUnitsPerSegment(0.5) 
    elif scaleBar_total_size <=  50000:
        scaleBar.setUnits(QgsUnitTypes.DistanceKilometers)
        scaleBar.setUnitLabel("km")
        scaleBar.setUnitsPerSegment(2.5)
    scaleBar.setBackgroundEnabled(1) # 0 pour ne pas avoir de background/fond
    layout.addLayoutItem(scaleBar)
    scaleBar.attemptMove(QgsLayoutPoint(5, 195, QgsUnitTypes.LayoutMillimeters)) # attention on se répère dans la map !
     
    # Fleche nord
    fleche_nord= QgsLayoutItemPicture(layout)
    image_fleche_nord = getThemeIcon("Nord.jpg")
    fleche_nord.setPicturePath(image_fleche_nord)
    layout.addLayoutItem(fleche_nord)
    fleche_nord.attemptResize(QgsLayoutSize(20, 20, QgsUnitTypes.LayoutMillimeters))
    fleche_nord.attemptMove(QgsLayoutPoint(275, 4, QgsUnitTypes.LayoutMillimeters))
    
    # légende
    
    legend = QgsLayoutItemLegend(layout)
    title_style = QgsLegendStyle()  # make new style
    title_style.setFont(QFont("Arial",12,1,False))
    legend.setStyle(QgsLegendStyle.Title,title_style) # set style to the legend title
    legend.setTitle("Legende")
    legend.setFrameEnabled(True)
    legend.setFrameStrokeWidth(QgsLayoutMeasurement(0.4))
    layerTree = QgsLayerTree()

    layerTree.addLayer(couche_zonage_concernee)
    legend.model().setRootGroup(layerTree)
    ############################################################################
    # pour en savoir plus:
    # https://hg-map.fr/tutos/73-qgis-et-python?start=5
    # https://library.virginia.edu/data/articles//how-to-create-and-export-print-layouts-in-python-for-qgis-3
    # https://github.com/epurpur/PyQGIS-Scripts/blob/master/CreateLayoutManagerAndExport.py
    # https://api.qgis.org/api/classQgsLegendStyle.html#acae0c6c735f4cb36f30fc53df74bd84e%20to%20change%20styles%20for%20other%20legend%20blocks%20(match%20%22Fonts%20and%20Text%20Formatting%22%20section)
    # https://qgis.org/pyqgis/3.28/core/QgsLegendStyle.html
    # https://api.qgis.org/api/classQgsLegendStyle.html#a56a491c6b4fad6c112c687c4a57dde6d
    # https://gis.stackexchange.com/questions/452695/setting-layout-legend-style-in-pyqgis
    #
    ##################################################################################################
    legend.setLinkedMap(map) # map is an instance of QgsLayoutItemMap
    layout.addLayoutItem(legend)
    legend.setColumnSpace(35)
    y=35
    x=220
    legend.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))

    # ajout d'un polygone
    # create
    polygon = QPolygonF()
    polygon.append(QPointF(2.0, 2.0))
    polygon.append(QPointF(295.0, 2.0)) # A4 = 297 de largeur en paysage
    polygon.append(QPointF(295.0, 25.0))
    polygon.append(QPointF(2.0, 25.0))
    polygon.append(QPointF(2.0, 2.0))
    mon_polygone = QgsLayoutItemPolyline(polygon,layout)
    layout.addLayoutItem(mon_polygone)
    # style
    props = {}
    props["color"] = "0,5,0,55"
    props["width"] = "2.0"
    props["capstyle"] = "square"
    props["style"] = "solid"
    props["style_border"] = "solid"
    props["color_border"] = "black"
    props["width_border"] = "1.0"
    props["joinstyle"] = "miter"
    style = QgsLineSymbol.createSimple(props)
    mon_polygone.setSymbol(style)

    # copyrigth couches fond de plans:
    cadastre='©IGN – PCI_EXPRESS – 2022\n'
    base='Sources des fonds cartographiques: \n'
    if id_liste_modalite== 0 and modalite_fond_de_carte:
        texte_FDP=base+cadastre+'©IGN - SCAN25® Version 1'
    elif id_liste_modalite== 1 and modalite_fond_de_carte:
        texte_FDP=base+cadastre+'©IGN – BDORTHO® - PVA 2018'
    else: 
        texte_FDP=base+cadastre
    copyrigth_FDP = QgsLayoutItemLabel(layout)
    copyrigth_FDP.setText(texte_FDP)
    copyrigth_FDP.setFont(QFont("Arial", 10))
    copyrigth_FDP.adjustSizeToText()
    layout.addLayoutItem(copyrigth_FDP)
    copyrigth_FDP.attemptResize(QgsLayoutSize(40, 20, QgsUnitTypes.LayoutMillimeters))
    copyrigth_FDP.attemptMove(QgsLayoutPoint(250,120, QgsUnitTypes.LayoutMillimeters))
        
    # logo administration
    # un cadre est ajouté par défaut au label pour le supprimer :
    # logo.setFrameEnabled(False)
    logo = QgsLayoutItemPicture(layout)
    Marianne_ddt21 = getThemeIcon("PREF_Cote_d_Or_CMJN_295_432px_Marianne.jpg")
    logo.setPicturePath(Marianne_ddt21)
    layout.addLayoutItem(logo)
    logo.attemptResize(QgsLayoutSize(50, 50, QgsUnitTypes.LayoutMillimeters))
    logo.attemptMove(QgsLayoutPoint(250, 150, QgsUnitTypes.LayoutMillimeters))
    
    # copyrigth DDT
    date=datetime.strftime(datetime.now(), "%d/%m/%Y")
    credit_text = QgsLayoutItemLabel(layout)
    credit_text.setText("© DDT21 le "+str(date))
    credit_text.setFont(QFont("Arial", 10))
    credit_text.adjustSizeToText()
    layout.addLayoutItem(credit_text)
    credit_text.attemptResize(QgsLayoutSize(40, 20, QgsUnitTypes.LayoutMillimeters))
    credit_text.attemptMove(QgsLayoutPoint(250,200, QgsUnitTypes.LayoutMillimeters))
    
    # this creates a QgsLayoutExporter object:
    exporter= QgsLayoutExporter(layout) 
    exporter.layout().refresh() # Refresh the layout before printing
    nom_du_fichier_carte_pdf= id_carte +'.pdf'
    pdf_path = os.path.join(chemin, nom_du_fichier_carte_pdf)
    exporter.exportToPdf(pdf_path, QgsLayoutExporter.PdfExportSettings())   # this exports a pdf of the layout object
        
    nom_du_fichier_carte_jpeg= id_carte +'.jpeg'
    jpeg_path = os.path.join(chemin, nom_du_fichier_carte_jpeg)
    # this exports an image of the layout object
    exporter.exportToImage(jpeg_path, QgsLayoutExporter.ImageExportSettings())
    
    return layout, manager, layoutName


def Gestion_visibilite_des_couches_vecteurs(nom_de_la_couche_de_zonage,groupe_de_la_couche_de_zonage):
    root = QgsProject.instance().layerTreeRoot() 
    groupe_zonage=root.findGroup(groupe_de_la_couche_de_zonage)
    couche_zonage_concernee= QgsVectorLayer()
    if groupe_zonage is not None:
        # on allume le groupe !
        groupe_zonage.setItemVisibilityChecked(True) 
        for child in groupe_zonage.children():
            nom_zonage_projet=child.name()
            if nom_zonage_projet == nom_de_la_couche_de_zonage:
                couche_zonage_concernee = QgsProject.instance().mapLayersByName(nom_de_la_couche_de_zonage)[0]
                QgsProject.instance().layerTreeRoot().findLayer(couche_zonage_concernee.id()).setItemVisibilityChecked(True)
    return groupe_zonage,couche_zonage_concernee
    
def Gestion_visibilite_des_couches_rasters(nom_du_raster,groupe_du_raster):
    root = QgsProject.instance().layerTreeRoot() 
    groupe_concerne=root.findGroup(groupe_du_raster)
    couche_concernee= QgsRasterLayer()
    if groupe_concerne is not None:
        # on allume le groupe !
        groupe_concerne.setItemVisibilityChecked(True) 
        for child in groupe_concerne.children():
            nom_zonage_projet=child.name()
            if nom_zonage_projet == nom_du_raster:
                couche_concernee = QgsProject.instance().mapLayersByName(nom_du_raster)[0]
                QgsProject.instance().layerTreeRoot().findLayer(couche_concernee.id()).setItemVisibilityChecked(True)
    return groupe_concerne,couche_concernee
    
def Gestion_extinction_des_couches_rasters(nom_du_raster,groupe_du_raster):
    root = QgsProject.instance().layerTreeRoot() 
    groupe_concerne=root.findGroup(groupe_du_raster)
    couche_concernee= QgsRasterLayer()
    if groupe_concerne is not None:
        groupe_concerne.setItemVisibilityChecked(True) 
        for child in groupe_concerne.children():
            nom_zonage_projet=child.name()
            if nom_zonage_projet == nom_du_raster:
                couche_concernee = QgsProject.instance().mapLayersByName(nom_du_raster)[0]
                QgsProject.instance().layerTreeRoot().findLayer(couche_concernee.id()).setItemVisibilityChecked(False)
    return groupe_concerne,couche_concernee
    
def Export_rapport_pdf(path_name,DicoR,liste_rubriques,projet,manager):
    # creation du titre de l'export 
    Rapport=DicoR
    titre="Rapport ADS d'interrogation des parcelles :\n"
    
    # #############################################################
    #
    # Combien de pages pour ce rapport ?
    # depend des rubriques et des couches, des saut de lignes...
    # 
    ###############################################################
    
    # la feuille A4 portrait mesure 210mm en largeur et 297mm en hauteur   
    # Les titres en ("Arial",14))
    # toto sera une ligne de texte en TextCustom.setFont(QFont("Verdana", 10))
    # on commence sous le rectangle à 27mm sur  297mm total
    # le texte commence à 60mm, on se donne une ligne 10mm, donc début à 6 lignes interligne ? 
    # d'après premiers tests d'impression il y a environ 50-60 lignes avec les paramètres en cours au 2024 02 22
    
    #############################################################################################
    # Composition du Texte et répartition sur p pages  d'après un dictionnaire des page
    #############################################################################################
    Dico_pages={}
    num_page=0
    counter_lignes_tot=0
    counter_lignes=0 
    # https://qgis.org/pyqgis/3.28/core/QgsLayoutItemTextTable.html
    first_page=True
    toto=''
    titi=''# point de redémarrage du texte dans nouvelle page
    nb_lignes_page=50
    for key in sorted(DicoR.keys()):
        Parcelle_id=str(key)
        nom_commune=str(DicoR[key][0])
        insee=str(DicoR[key][1])
        code_section=str(DicoR[key][2])
        feuille=str(DicoR[key][3])
        num_parcelle=str(DicoR[key][4])
        Liste_des_zonages_et_assiettes_concernes=DicoR[key][5]
        dico_attributs_zone_parcelle=(DicoR[key][7])
        toto=toto+'La parcelle: '+ str(num_parcelle)+' ,section:'+str(code_section)+' ,feuille:'+str(feuille)+' commune de '+str(nom_commune)+' (insee:'+str(insee)+')'
        toto=toto+' est concernée par: \n\n'
        titi='La parcelle: '+ str(num_parcelle)+' ,section:'+str(code_section)+' ,feuille:'+str(feuille)+' commune de '+str(nom_commune)+' (insee:'+str(insee)+')'
        titi=titi+' est concernée par: \n\n'
        counter_lignes+=3
        counter_lignes_tot+=3
        
        for idx,rubrique in enumerate(liste_rubriques):
            first_rubrique=True      
            for key_zone in list(dico_attributs_zone_parcelle.keys()): # on a en  effet parfois plusieurs zones pour une thematique
                id_zonage=str(key_zone)
                Couche_Donnee=str(dico_attributs_zone_parcelle[key_zone][0])
                Grpt_Thema=dico_attributs_zone_parcelle[key_zone][2]
                Thematique=dico_attributs_zone_parcelle[key_zone][3]
                if rubrique == Grpt_Thema :
                    if first_rubrique:
                        first_rubrique=False
                        toto=toto+str(rubrique)+':\n'
                        titi=titi+str(rubrique)+':\n'
                        counter_lignes+=1
                        counter_lignes_tot+=1
                    toto=toto+"              - " + Couche_Donnee +'\n'
                    titi=titi+"              - " + Couche_Donnee +'\n'
                    counter_lignes+=1
                    counter_lignes_tot+=1
                    if counter_lignes>nb_lignes_page: # on teste si on est encore dans la page
                        if first_page: # on teste si c'est la première page pour laquelle on limite le nombre de ligne
                            first_page=False
                            counter_lignes=0
                            nb_lignes_page=58
                        else: counter_lignes=0
                        Dico_pages[num_page]=[tutu,counter_lignes] # on sauvegarde le texte avant l'ajout qui fait sortir de la page, cad tutu
                        num_page+=1 # on passe à une nouvelle page
                        # avec cette dernière zone on est sortie de la page on repart avec cette zone dans titi :
                        toto=titi # on repart avec les dernières lignes ajoutées qui aurait dépassées de la page
                    else: 
                        titi=''
                        tutu=toto # on a n'a pas depassé la page, on garde toto dans tutu
        toto=toto+' -----------------------------------------------------------------------------------------------------------  ' +'\n\n' 
        counter_lignes+=3
        counter_lignes_tot+=3
    tutu=toto+'------------------------------     Fin du Rapport     ------------------------------' +'\n\n'
    Dico_pages[num_page]=[tutu,counter_lignes]
    nb_pages_A4_necessaire=num_page+1 # car on part de num-page à zero !
    #####################"fin calcul nb pages et fabrication de leurs contenus ##############################
 
    project=projet
    date_H_M=datetime.strftime(datetime.now(), "%Y_%m_%d_%Hh_%Mmin")
    layoutName = 'Rapport_interrogation_ADS_'+str(date_H_M)
    # on doit vérifier et éventuellement dézingier tous les derniers layout pour se prémunir des erreurs si un layout.name() existe déjà !
    layouts_list = manager.printLayouts()
    for layout in layouts_list:
        if layout.name() == layoutName:
            manager.removeLayout(layout)
  
    layout = QgsPrintLayout(project)  #makes a new print layout object, takes a QgsProject as argument
    layout.initializeDefaults()  #create default map canvas
    layout.setName(layoutName)
     # on ajoute un layout ayant nom de la couche
    manager.addLayout(layout)

    #https://gis.stackexchange.com/questions/325360/how-to-change-page-orientation-and-number-of-pages-of-print-composer-layout-usin
    #https://gis.stackexchange.com/questions/383884/adding-page-to-layout-after-populating-the-page-using-pyqgis    
    # impression des différentes pages en parcourant le dictionnaire et en plaçant dans la "bonne page" le texte
    # c'est ce que permet l'argument page de TextCustom.attemptMove()
    # voir https://gis.stackexchange.com/questions/383884/adding-page-to-layout-after-populating-the-page-using-pyqgis
    # https://gis.stackexchange.com/questions/388573/repeat-a-qgslayoutitem-on-several-pages-without-using-atlas
    toto_Final=''
    pc = layout.pageCollection()
        
    #for key_page in list(Dico_pages.keys()):
    for key_page in sorted(Dico_pages.keys()):
        num_page=int(key_page)
              
        page = QgsLayoutItemPage(layout)
        page.setPageSize('A4',  QgsLayoutItemPage.Portrait)
        #page.setPageSize('A4',  QgsLayoutItemPage.Orientation.Portrait)
        #page.setPageSize('A4',  QgsLayoutItemPage.Orientation.Landscape)
        pc.addPage(page) # inserrons les nouvelles pages 
        pc.page(num_page).setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait) 
        
        count_lignes=str(Dico_pages[key_page][1])
        toto_Final=Dico_pages[key_page][0]
        #QMessageBox.information(None,"DEBUG:","key_page n: "+ str(key_page)+"\nDico_pages[key_page][0] : \n"+ toto_Final+"\ncount_lignes : "+str(count_lignes))
        # Ajout d'un Texte 
        TextCustom = QgsLayoutItemLabel(layout)
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Verdana"))
        text_format.setSize(9)
        TextCustom.setTextFormat(text_format)
   
        if num_page==0 :
            # on décalle le début du texte sur la page 0 par rapport au rectangle contenant le titre
            TextCustom.attemptMove(QgsLayoutPoint(10,35, QgsUnitTypes.LayoutMillimeters),page=num_page)
            TextCustom.setText(toto_Final)
            layout.addLayoutItem(TextCustom)
            ###########################################"
            # Titre de la carte
            title = QgsLayoutItemLabel(layout)
            title.setText(titre)
            # title.setFont(QFont("Verdana",28))
            title.setFont(QFont("Arial",14))
            # https://gis.stackexchange.com/questions/459233/setting-width-for-label-adjustsizetotext-in-pyqgis
            y=7
            x=10
            title.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
            title.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters),page=0)
            layout.addLayoutItem(title)
                  
            # ajout d'un polygone autour du titre
            polygon = QPolygonF()
            polygon.append(QPointF(2.0, 2.0))
            polygon.append(QPointF(205.0, 2.0)) # A4 = 210 de largeur en portrait
            polygon.append(QPointF(205.0, 25.0))
            polygon.append(QPointF(2.0, 25.0))
            polygon.append(QPointF(2.0, 2.0))
            mon_polygone = QgsLayoutItemPolyline(polygon,layout)
            # modifions  le style du polygone
            props = {}
            props["color"] = "0,5,0,55"
            props["width"] = "2.0"
            props["capstyle"] = "square"
            props["style"] = "solid"
            props["style_border"] = "solid"
            props["color_border"] = "black"
            props["width_border"] = "1.0"
            props["joinstyle"] = "miter"
            style = QgsLineSymbol.createSimple(props)
            mon_polygone.setSymbol(style) 
            layout.addLayoutItem(mon_polygone)
            mon_polygone.attemptMove(QgsLayoutPoint(2, 2, QgsUnitTypes.LayoutMillimeters),page=0)

        else:
            TextCustom.attemptMove(QgsLayoutPoint(10,20),page=num_page)
            TextCustom.setText(toto_Final)
            layout.addLayoutItem(TextCustom)
       
        # Numero de page
        texte_page = 'page' + str(num_page+1) + '/' + str(nb_pages_A4_necessaire)
        page_text = QgsLayoutItemLabel(layout)
        page_text.setFont(QFont("Ms Shell Dlg 2", 8))
        page_text.attemptMove(QgsLayoutPoint(193, 285),page=num_page)
        page_text.setHAlign(Qt.AlignRight)
        page_text.setMinimumSize(QgsLayoutSize(15, 8, QgsUnitTypes.LayoutMillimeters))
        page_text.setText(texte_page)
        layout.addLayoutItem(page_text)
        
        # logo administration
        # un cadre est ajouté par défaut au label pour le supprimer :
        # logo.setFrameEnabled(False)
        logo = QgsLayoutItemPicture(layout)
        Marianne_ddt21 = getThemeIcon("PREF_Cote_d_Or_CMJN_295_432px_Marianne.jpg")
        logo.setPicturePath(Marianne_ddt21)
        layout.addLayoutItem(logo)
        logo.attemptResize(QgsLayoutSize(30, 30, QgsUnitTypes.LayoutMillimeters))
        logo.attemptMove(QgsLayoutPoint(180, 230, QgsUnitTypes.LayoutMillimeters),page=num_page)
        
        # copyrigth DDT
        date=datetime.strftime(datetime.now(), "%d/%m/%Y")
        credit_text = QgsLayoutItemLabel(layout)
        credit_text.setText("© DDT21 le "+str(date))
        credit_text.setFont(QFont("Arial", 7))
        credit_text.adjustSizeToText()
        layout.addLayoutItem(credit_text)
        credit_text.attemptResize(QgsLayoutSize(30, 15, QgsUnitTypes.LayoutMillimeters))
        credit_text.attemptMove(QgsLayoutPoint(175,280, QgsUnitTypes.LayoutMillimeters),page=num_page)

    #############################################################################################
    
    # this creates a QgsLayoutExporter object:
    exporter= QgsLayoutExporter(layout) 
    # Refresh the layout before printing
    exporter.layout().refresh()
    # setup settings
    settingsPdf = QgsLayoutExporter.PdfExportSettings()
    settingsPdf.dpi = 300

    nom_du_fichier_tableau_pdf = 'Rapport_interrogation_ADS_'+str(date_H_M)+'.pdf'
    pdf_path = os.path.join(path_name, nom_du_fichier_tableau_pdf)
    # this exports a pdf of the layout object
    exporter.exportToPdf(pdf_path, settingsPdf)
     
    return layout, manager, layoutName
    
def layout_cleaner(project):
    project = QgsProject.instance()   #gets a reference to the project instance
    manager = project.layoutManager() #gets a reference to the layout manager
    layout = QgsPrintLayout(project)   #makes a new print layout object, takes a QgsProject as argument
    layouts_list = manager.printLayouts()
    for layout in layouts_list:
        manager.removeLayout(layout)
    manager.clear()
        
        
def Exports_GeoPDF(path_name,rapport_name,projet,manager,rec_emprise,liste_noms_couches_intersectees):
    # pour en savoir plus:
    # https://north-road.com/2019/09/03/qgis-3-10-loves-geopdf/
    # https://qgis.org/pyqgis/3.28/
    # https://www.cadlinecommunity.co.uk/hc/en-us/articles/360003823717-QGIS-Creating-a-GeoPDF
    # https://qgis.org/pyqgis/3.28/core/QgsLayoutExporter.html#qgis.core.QgsLayoutExporter.PdfExportSettings.appendGeoreference
    # https://gis.stackexchange.com/questions/370656/can-i-create-a-geospatial-pdf-in-python-without-using-gis-software
   
    project=projet
    layouts_list = manager.printLayouts()
    liste_layout_names=[]
    
    for idx, lay in enumerate(layouts_list):
        liste_layout_names.append(lay.name())

    for layout in layouts_list:
        if layout.name() == layoutName:
            manager.removeLayout(layout)

    layout = QgsPrintLayout(project)            #makes a new print layout object, takes a QgsProject as argument
    layout.initializeDefaults()  #create default map canvas
    layoutName = str(rapport_name)
    layout.setName(layoutName)
     # on ajoute un layout ayant nom de la couche
    manager.addLayout(layout)
    
    # la feuille A4 paysage mesure 297mm en largeur et 210mm en hauteur   
    page = QgsLayoutItemPage(layout)
    page.setPageSize('A4',  QgsLayoutItemPage.Landscape)
    page_center = page.pageSize().width() / 2
    
    # Composeur d'impression: 
    # Tous les éléments de la mise page comme carte, étiquette, 
    # …sont des objets représentés par des classes qui héritent de la classe de base QgsLayoutItem.

    # Carte:
    # This adds a map item to the Print Layout 
    map = QgsLayoutItemMap(layout)
    map.setRect(20, 20, 20, 20)  
    # Set Extent
    canvas = iface.mapCanvas()

    rec=rec_emprise
    rectangle = QgsRectangle(rec[0],rec[1],rec[2],rec[3])  #an example of how to set map extent with coordinates
    map.setExtent(rectangle)
            
    # Move: les arguments sont:
    # la distance à partir du bord gauche du layout, 
    # puis la distance à partir du bord haut.
    map.attemptMove(QgsLayoutPoint(5, 26, QgsUnitTypes.LayoutMillimeters))
    map.attemptResize(QgsLayoutSize(240, 180, QgsUnitTypes.LayoutMillimeters))  # Resize :  QgsLayoutSize(largeur, hauteur , unités employées)
    map.zoomToExtent(iface.mapCanvas().extent())
    layout.addLayoutItem(map)
    
    # https://courses.spatialthoughts.com/pyqgis-in-a-day.html#turn-a-layer-onoff
    
    # Titre de la carte
    nom_de_la_carte=rapport_name 
    title = QgsLayoutItemLabel(layout)
    title.setText(nom_de_la_carte)
    # title.setFont(QFont("Verdana",28))
    title.setFont(QFont("Arial",13))
    # https://gis.stackexchange.com/questions/459233/setting-width-for-label-adjustsizetotext-in-pyqgis
    y=5
    x=7
    layout.addLayoutItem(title)
    title.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
    title.adjustSizeToText()
    y += title.boundingRect().height()
    title.attemptResize(QgsLayoutSize(x+title.boundingRect().width(),y))
    layout.addLayoutItem(title)
   
    # Echelle graphique
    # on prépare la taille de la sclebar avec Etendu_du_Canvas qui est un QgsRectangle
    # https://qgis.org/pyqgis/3.2/core/other/QgsRectangle.html 
    scaleBar = QgsLayoutItemScaleBar(layout)
    scaleBar.applyDefaultSettings()
    scaleBar.setLinkedMap(map)
    scaleBar.setStyle('Single Box')  # setStyle: 'Single Box', 'Double Box', 'Line Ticks Middle', 'Line Ticks Down', 'Line Ticks Up', 'Numeric'
    scaleBar.setNumberOfSegmentsLeft(0)
    scaleBar.setNumberOfSegments(2)
    # on choisir d'avoir toujours deux segments dans l'échelle ... quelle doit etre la taille d'un segment ?
    Etendu_du_Canvas=canvas.extent()
    H_Canvas=Etendu_du_Canvas.height()
    L_Canvas=Etendu_du_Canvas.width()
    if H_Canvas > L_Canvas: 
        Dmax_Canvas=H_Canvas
    else:
        Dmax_Canvas=L_Canvas
    # on va se donner comme taille de la barre d'échelle 1/5 de la taille maximale de l'étendue du Canevas de la carte
    scaleBar_total_size=int(Dmax_Canvas/5)
    scaleBar.setMapUnitsPerScaleBarUnit(1)  # Sets the number of map units per scale bar unit used by the scalebar:
    if scaleBar_total_size <= 100:
        scaleBar.setUnits(QgsUnitTypes.DistanceMeters)
        scaleBar.setUnitLabel("m")
        scaleBar.setUnitsPerSegment(25)
    elif scaleBar_total_size <= 500:
        scaleBar.setUnits(QgsUnitTypes.DistanceMeters)
        scaleBar.setUnitLabel("m")
        scaleBar.setUnitsPerSegment(100)
    elif scaleBar_total_size <=  1000:
        scaleBar.setUnits(QgsUnitTypes.DistanceMeters)
        scaleBar.setUnitLabel("m")
        scaleBar.setUnitsPerSegment(250)
    elif scaleBar_total_size <=  10000:
        scaleBar.setUnits(QgsUnitTypes.DistanceKilometers)
        scaleBar.setUnitLabel("km")
        scaleBar.setUnitsPerSegment(0.5) 
    elif scaleBar_total_size <=  50000:
        scaleBar.setUnits(QgsUnitTypes.DistanceKilometers)
        scaleBar.setUnitLabel("km")
        scaleBar.setUnitsPerSegment(2.5)
    scaleBar.setBackgroundEnabled(1) # 0 pour ne pas avoir de background/fond
    layout.addLayoutItem(scaleBar)
    scaleBar.attemptMove(QgsLayoutPoint(5, 195, QgsUnitTypes.LayoutMillimeters)) # attention on se répère dans la map !
     
    # Fleche nord
    fleche_nord= QgsLayoutItemPicture(layout)
    image_fleche_nord = getThemeIcon("Nord.jpg")
    fleche_nord.setPicturePath(image_fleche_nord)
    layout.addLayoutItem(fleche_nord)
    fleche_nord.attemptResize(QgsLayoutSize(20, 20, QgsUnitTypes.LayoutMillimeters))
    fleche_nord.attemptMove(QgsLayoutPoint(275, 4, QgsUnitTypes.LayoutMillimeters))
    
      
    #############################################################################
    # Ajout d'un cadre autour du titre
    
    cadre = QPolygonF()
    cadre.append(QPointF(2.0, 2.0))
    cadre.append(QPointF(295.0, 2.0)) # A4 = 297 de largeur en paysage
    cadre.append(QPointF(295.0, 25.0))
    cadre.append(QPointF(2.0, 25.0))
    cadre.append(QPointF(2.0, 2.0))
    mon_cadre = QgsLayoutItemPolyline(cadre,layout)
    layout.addLayoutItem(mon_cadre)
    # style
    props = {}
    props["color"] = "0,5,0,55"
    props["width"] = "2.0"
    props["capstyle"] = "square"
    props["style"] = "solid"
    props["style_border"] = "solid"
    props["color_border"] = "black"
    props["width_border"] = "1.0"
    props["joinstyle"] = "miter"
    style = QgsLineSymbol.createSimple(props)
    mon_cadre.setSymbol(style)

    # copyrigth couches fond de plans:
    base='Sources des fonds cartographiques: \n'
    cadastre='©IGN – PCI_EXPRESS – 2022\n'
    texte_FDP=base+cadastre+'©IGN - SCAN25® Version 1 \n'+'©IGN – BDORTHO® - PVA 2018'
    copyrigth_FDP = QgsLayoutItemLabel(layout)
    copyrigth_FDP.setText(texte_FDP)
    copyrigth_FDP.setFont(QFont("Arial", 7))
    copyrigth_FDP.adjustSizeToText()
    layout.addLayoutItem(copyrigth_FDP)
    copyrigth_FDP.attemptResize(QgsLayoutSize(40, 20, QgsUnitTypes.LayoutMillimeters))
    copyrigth_FDP.attemptMove(QgsLayoutPoint(250,150, QgsUnitTypes.LayoutMillimeters))
        
    # logo administration
    # un cadre est ajouté par défaut au label pour le supprimer :
    # logo.setFrameEnabled(False)
    logo = QgsLayoutItemPicture(layout)
    Marianne_ddt21 = getThemeIcon("PREF_Cote_d_Or_CMJN_295_432px_Marianne.jpg")
    logo.setPicturePath(Marianne_ddt21)
    layout.addLayoutItem(logo)
    logo.attemptResize(QgsLayoutSize(30, 30, QgsUnitTypes.LayoutMillimeters))
    logo.attemptMove(QgsLayoutPoint(255, 165, QgsUnitTypes.LayoutMillimeters))
    
    # copyrigth DDT
    date=datetime.strftime(datetime.now(), "%d/%m/%Y")
    credit_text = QgsLayoutItemLabel(layout)
    # credit_text.setText("© DDT21 le:"+'\n'+str(date))
    credit_text.setText("© DDT21 le: "+str(date))
    credit_text.setFont(QFont("Arial", 10))
    credit_text.adjustSizeToText()
    layout.addLayoutItem(credit_text)
    credit_text.attemptResize(QgsLayoutSize(40, 20, QgsUnitTypes.LayoutMillimeters))
    credit_text.attemptMove(QgsLayoutPoint(250,200, QgsUnitTypes.LayoutMillimeters))
    
    ###########################################
    #                   légende
    ##########################################
    # on veut gérer le cartouche legende en fonction du nombre de figurés des analyses thématiques des layers
    # si ca ne rentre pas en une colonne dans le geopdf A4 paysage, on déporte sur autre pdf ce taille A4,A3 ou A0
    #################################
    # https://hg-map.fr/tutos/73-qgis-et-python?start=5
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("Legende")
   
    # https://library.virginia.edu/data/articles//how-to-create-and-export-print-layouts-in-python-for-qgis-3
    # https://github.com/epurpur/PyQGIS-Scripts/blob/master/CreateLayoutManagerAndExport.py
    # on ne veut que la légende de la couche de zonage active....
    # Checks layer tree objects and stores them in a list. This includes csv tables
    # checked_layers = [layer.name() for layer in QgsProject().instance().layerTreeRoot().children() if layer.isVisible()]
    # get map layer objects of checked layers by matching their names and store those in a list
    checked_layers=liste_noms_couches_intersectees
    layersToAdd = [layer for layer in QgsProject().instance().mapLayers().values() if layer.name() in checked_layers]
    root = QgsLayerTree()
    for layer in layersToAdd:
        root.addLayer(layer) #add layer objects to the layer tree
    legend.model().setRootGroup(root)
    
    ###############################################################
    # comment compter le nombre de figurés des différentes couches pour gerer la publication des legendes ?
    # https://gis.stackexchange.com/questions/464170/adjust-symbol-size-for-color-ramp-in-print-layout-legend-with-python
    nb_items_legendes=0
    for layer in layersToAdd:
        tree_view = iface.layerTreeView()
        model = tree_view.layerTreeModel()
        layer_tree = model.rootGroup().findLayer(layer.id()) 
        legend_items = model.layerLegendNodes(layer_tree)
        nb_items=len(legend_items) # on a donc le nombre d'items d'une couche 
        nb_items_legendes+= nb_items
        
    #############
    if nb_items_legendes < 13: # si la legende prend plus de 12 lignes on la déporte dans un autre pdf car sinon elle déborde du geopdf
        style = QgsLegendStyle()  # make new style
        style.setFont(QFont("Arial",7,1,False))
        legend.setStyle(QgsLegendStyle.Group,style)
        style_base = QgsLegendStyle()  # make new style
        style_base.setFont(QFont("Arial",6,1,False))
        legend.setStyle(QgsLegendStyle.SymbolLabel,style_base)
        legend.rstyle(QgsLegendStyle.Symbol).setMargin( QgsLegendStyle.Top , 4) # pour decaller le texte du symbole
        
        legend.setLinkedMap(map) # map is an instance of QgsLayoutItemMap
        legend.setLegendFilterByMapEnabled(True) # pour n'avoir que les nodes de lé legende dans l'emprise
        legend.refresh()
        layout.addLayoutItem(legend)
        legend.setColumnSpace(35)
        y=25
        x=220
        legend.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
    else: # si il y a plus de 12 items dans une legende on l'exporte à part !
        Export_Legende_pdf(path_name,rapport_name,projet,manager,liste_noms_couches_intersectees,nb_items_legendes)
    
    exporter= QgsLayoutExporter(layout) # this creates a QgsLayoutExporter object
    exporter.layout().refresh() # Refresh the layout before printing
    # setup settings
    settings =  QgsLayoutExporter.PdfExportSettings()
    settings.dpi =90 # 300
    # pour créer un geopdf !
    # https://api.qgis.org/api/3.28/structQgsLayoutExporter_1_1PdfExportSettings.html#a93ddb66c1e1f541a1bed511a41f9e396
    settings.writeGeoPdf = True
        
    date_H_M=datetime.strftime(datetime.now(), "%Y_%m_%d_%Hh_%Mmin")
    file_rapport= str(path_name)
    path_rapport=file_rapport.replace("\\","/")
    nom_export="Rapport_cartographique_d_interrogation_ADS_des_parcelles_"
    nom_du_fichier_tableau_pdf = nom_export+str(date_H_M)+'.pdf'
    
    pdf_path = os.path.join(path_rapport, nom_du_fichier_tableau_pdf)
    exporter.exportToPdf(pdf_path, settings)
    
    return layout, manager, layoutName,nb_items_legendes,liste_noms_couches_intersectees

def Export_Legende_pdf(path_name,rapport_name,projet,manager,liste_noms_couches_intersectees,nb_items_legendes):
    project=projet
    """
    layouts_list = manager.printLayouts()
    # nettoyage des layouts
    # on doit vérifier et éventuellement dézingier tous les derniers layout pour se prémunir des erreurs si un layout.name() existe déjà !
    # nettoyage des layouts
    for layout in layouts_list:
        manager.removeLayout(layout)
    """
    # creation d'un nouveau layout
    layout_legende= QgsPrintLayout(project)  #makes a new print layout object, takes a QgsProject as argument
    layout_legende.initializeDefaults()  #create default map canvas
    date_H_M=datetime.strftime(datetime.now(), "%Y_%m_%d_%Hh_%Mmin")
    layout_legende_Name = 'Rapport_interrogation_ADS_Legendes_'+str(date_H_M)
    layout_legende.setName(layout_legende_Name)
     # on ajoute un layout ayant nom de la couche
    manager.addLayout(layout_legende)
  
    # on va faire une page de taille adpatée aux nombres d'items des analyses thématiques des légendes
    page = QgsLayoutItemPage(layout_legende)
    pc = layout_legende.pageCollection()
    page = QgsLayoutItemPage(layout_legende)
    page.setPageSize('A4',  QgsLayoutItemPage.Portrait)
    pc.addPage(page) # inserrons les nouvelles pages 
           
    if nb_items_legendes <30: # A4
        lmax_polygone=285
        xlogo,ylogo=260,160
        xdate,ydate=250,20
        xlegend,ylegend=15,30
        # la feuille A4 portrait mesure 210mm en largeur et 297mm en hauteur 
        #page.setPageSize('A4',  QgsLayoutItemPage.Orientation.Portrait)
        page.setPageSize('A4',  QgsLayoutItemPage.Orientation.Landscape)
        pc = layout_legende.pageCollection()
        pc.page(0).setPageSize('A4', QgsLayoutItemPage.Orientation.Landscape)
        
    elif nb_items_legendes <60: # A3
        lmax_polygone=415
        xlogo,ylogo=390,260
        xdate,ydate=370,20
        xlegend,ylegend=15,30
        # Dimension A3	297 x 420 mm	
        #page.setPageSize('A3',  QgsLayoutItemPage.Orientation.Portrait)
        page.setPageSize('A3',  QgsLayoutItemPage.Orientation.Landscape)
        pc = layout_legende.pageCollection()
        pc.page(0).setPageSize('A3', QgsLayoutItemPage.Orientation.Landscape)
        
    else: # A0
        lmax_polygone=14035
        xlogo,ylogo=1159,800 
        xdate,ydate=1140,20
        xlegend,ylegend=15,30
        # Dimension A0	841 x 1189 mm	9933 x 14043 px
        #page.setPageSize('A0',  QgsLayoutItemPage.Orientation.Portrait)
        page.setPageSize('A0',  QgsLayoutItemPage.Orientation.Landscape)
        pc = layout_legende.pageCollection()
        pc.page(0).setPageSize('A0', QgsLayoutItemPage.Orientation.Landscape)
   
    # Titre de la carte
    titre="Ensemble des légendes du Géo-PDF :"
    title = QgsLayoutItemLabel(layout_legende)
    title.setText(titre)
    title.setFont(QFont("Arial",14))
    layout_legende.addLayoutItem(title)
    xtitre,ytitre=10,7
    title.attemptMove(QgsLayoutPoint(xtitre,ytitre, QgsUnitTypes.LayoutMillimeters))
    title.adjustSizeToText()
    ytitre += title.boundingRect().height()
    xtitre += title.boundingRect().width()
    # set a fixed width for the title
    title.attemptResize(QgsLayoutSize(xtitre,ytitre))

    # ajout d'un polygone
    # create
    polygon = QPolygonF()
    polygon.append(QPointF(2.0, 2.0))
    polygon.append(QPointF(lmax_polygone, 2.0)) 
    polygon.append(QPointF(lmax_polygone, 25.0))
    polygon.append(QPointF(2.0, 25.0))
    polygon.append(QPointF(2.0, 2.0))
    mon_polygone = QgsLayoutItemPolyline(polygon,layout_legende)
    layout_legende.addLayoutItem(mon_polygone)
    # style
    props = {}
    props["color"] = "0,5,0,55"
    props["width"] = "2.0"
    props["capstyle"] = "square"
    props["style"] = "solid"
    props["style_border"] = "solid"
    props["color_border"] = "black"
    props["width_border"] = "1.0"
    props["joinstyle"] = "miter"
    style = QgsLineSymbol.createSimple(props)
    mon_polygone.setSymbol(style)
    ###############################################################################
    # légende
    # https://hg-map.fr/tutos/73-qgis-et-python?start=5
    legend = QgsLayoutItemLegend(layout_legende)
    # on ajoute pas de carte/ map mais besoin pour filtrer les legendes
    map = QgsLayoutItemMap(layout_legende)
    # link it with the legend before enabling the filtering:
    legend.setLinkedMap(map) # pass a QgsLayoutItemMap object
    legend.setLegendFilterByMapEnabled(True) # pour n'avoir que les nodes des éléments des legendes dans l'emprise
    legend.refresh()
    legend.setTitle("Legende")
    # legend.attemptSetSceneRect(QRectF(120, 20, 80, 80))
    legend.setFrameEnabled(True)
    legend.setFrameStrokeWidth(QgsLayoutMeasurement(0.4))
    # https://library.virginia.edu/data/articles//how-to-create-and-export-print-layouts-in-python-for-qgis-3
    # https://github.com/epurpur/PyQGIS-Scripts/blob/master/CreateLayoutManagerAndExport.py
    # on ne veut que la légende de la couche de zonage active....
    # Checks layer tree objects and stores them in a list. This includes csv tables
    # checked_layers = [layer.name() for layer in QgsProject().instance().layerTreeRoot().children() if layer.isVisible()]
    # get map layer objects of checked layers by matching their names and store those in a list
    checked_layers=liste_noms_couches_intersectees
    layersToAdd = [layer for layer in QgsProject().instance().mapLayers().values() if layer.name() in checked_layers]
    root = QgsLayerTree()
    for layer in layersToAdd:
        root.addLayer(layer) #add layer objects to the layer tree
    legend.model().setRootGroup(root)
    # https://api.qgis.org/api/classQgsLegendStyle.html#acae0c6c735f4cb36f30fc53df74bd84e%20to%20change%20styles%20for%20other%20legend%20blocks%20(match%20%22Fonts%20and%20Text%20Formatting%22%20section)
    # style.set...(...)
    style = QgsLegendStyle()  # make new style
    style.setFont(QFont("Arial",7,1,False))
 
    legend.setStyle(QgsLegendStyle.Group,style)
    style_base = QgsLegendStyle()  # make new style
    style_base.setFont(QFont("Arial",6,1,False))
    legend.setStyle(QgsLegendStyle.SymbolLabel,style_base)

    layout_legende.addLayoutItem(legend)
    legend.setColumnCount(3) # https://qgis.org/pyqgis/3.28/core/QgsLegendSettings.html#qgis.core.QgsLegendSettings.setColumnCount
    legend.setColumnSpace(5) # https://qgis.org/pyqgis/3.28/core/QgsLegendSettings.html#qgis.core.QgsLegendSettings.columnSpace
    legend.attemptMove(QgsLayoutPoint(xlegend,ylegend, QgsUnitTypes.LayoutMillimeters))

    # logo administration
    # un cadre est ajouté par défaut au label pour le supprimer :
    # logo.setFrameEnabled(False)
    logo = QgsLayoutItemPicture(layout_legende)
    Marianne_ddt21 = getThemeIcon("PREF_Cote_d_Or_CMJN_295_432px_Marianne.jpg")
    logo.setPicturePath(Marianne_ddt21)
    layout_legende.addLayoutItem(logo)
    logo.attemptResize(QgsLayoutSize(30, 30, QgsUnitTypes.LayoutMillimeters))
    logo.attemptMove(QgsLayoutPoint(xlogo,ylogo, QgsUnitTypes.LayoutMillimeters)) # Dimension A0	841 x 1189 mm	9933 x 14043 px
    
    # copyrigth DDT
    date=datetime.strftime(datetime.now(), "%d/%m/%Y")
    credit_text = QgsLayoutItemLabel(layout_legende)
    credit_text.setText("© DDT21 le "+str(date))
    credit_text.setFont(QFont("Arial", 8))
    credit_text.adjustSizeToText()
    layout_legende.addLayoutItem(credit_text)
    credit_text.attemptResize(QgsLayoutSize(30, 15, QgsUnitTypes.LayoutMillimeters))
    credit_text.attemptMove(QgsLayoutPoint(xdate,ydate, QgsUnitTypes.LayoutMillimeters))# Dimension A0	841 x 1189 mm	9933 x 14043 px
    
    # this creates a QgsLayoutExporter object:
    exporter= QgsLayoutExporter(layout_legende) 
    # Refresh the layout_legende before printing
    exporter.layout().refresh()
    # setup settings
    settingsPdf = QgsLayoutExporter.PdfExportSettings()
    settingsPdf.dpi = 300
    
    nom_du_fichier_tableau_pdf = 'Legende_du_GeoPDF_interrogation_ADS_une_page_'+str(date_H_M)+'.pdf'
    pdf_path = os.path.join(path_name, nom_du_fichier_tableau_pdf)
    # this exports a pdf of the layout object
    exporter.exportToPdf(pdf_path, settingsPdf)
     
    return layout_legende, manager, layout_legende_Name
    
