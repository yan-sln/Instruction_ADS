import os
import csv
import shutil

from datetime import datetime
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsLayerTreeGroup, QgsLayerTreeLayer
import csv

from PyQt5.QtWidgets import QMessageBox
from qgis.utils import iface

from urllib.parse import unquote, urlparse

import zipfile
import xml.etree.ElementTree as ET # françois Thevand mail du 29 20 2024
from pathlib import *


# Exemple d'utilisation de la bibliothèque pathlib :
# your_file_root = Path("your_file_path").parent
# Nom du fichier sans l'extention : your_file_path.stem
# extention du fichier avec le . : your_file_path.suffix

# lecture de la balise SrcDataSource du qgz
#        tree = ET.parse("your_file_path")
#        root = tree.getroot()
#        for datasource in root.findall(".//SrcDataSource"):
#           src_file_rel = datasource.text
#          
#           src_file_abs = (your_file_root / src_file_rel).resolve()  # Chemin absolu du fichier source

def read_csv(csv_path):
    layers_info = []
    with open(csv_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            layers_info.append(row)
    return layers_info      
  

def get_project_layers(project):
    # project = QgsProject.instance()
    project_layers = [layer.name() for layer in project.mapLayers().values()]
    return project_layers

def get_file_modification_time(file_path):
    if os.path.exists(file_path):
        return datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    return None

def get_file_creation_time(file_path):
    # Récupérer la date de création du fichier
    if os.path.exists(file_path):
        return datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    return ''
    
def get_url(layer_object):
    # code pris dans le plugin project_report, fichier QProjectReport.py author=Patricio Soriano. SIGdeletras.com, email=pasoiano@gmail.com

    if isinstance(layer_object, QgsVectorLayer):
        path_url = layer_object.source()
    elif isinstance(layer_object, QgsRasterLayer) and layer_object.providerType() == 'gdal':
        path_url = layer_object.source()
    else:
        path_url = layer_object.source().split('url=')[1]
    return path_url

def get_original_source(layer_source):
    # Extraire le chemin du fichier original en ignorant les filtres
    if '|' in layer_source:
        original_source = layer_source.split('|')[0]
        return unquote(original_source)
    return unquote(layer_source)
    
def get_original_source_and_filter(layer_source):
    # Extraire le chemin du fichier original et les filtres
    if '|' in layer_source:
        original_source, filter_part = layer_source.split('|', 1)
        return unquote(original_source), '|' + filter_part
    return unquote(layer_source), ''
    
    
def remove_outputfolders(main_directory):
    #Remove all files and subfolders within a given folder, then remove the folder it
    #Parameters:
    #main_directory (str): the path to the folder to be removed
     
    try:
        for root, dirs, files in os.walk(main_directory, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
            os.rmdir(main_directory)
    except OSError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        
def copy_shapefile_components(src_path, dst_dir):
    # Liste des extensions de fichiers associés à un shapefile
    shapefile_extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qml', '.sbn', '.sbx', '.fbn', '.fbx', '.ain', '.aih', '.ixs', '.mxs', '.atx', '.xml']

    # Convertir le Path en chaîne de caractères pour utiliser replace
    src_path_str = str(src_path)

    # Vérifier la longueur du chemin source et destination
    if len(src_path_str) > 255 or len(dst_dir) > 255:
        QMessageBox.warning(
            None,
            "Erreur de chemin",
            "Le chemin du fichier source ou de destination est trop long (plus de 255 caractères).\n"
            "Le plugin sera lancé sans mise à jour des données."
        )
        return False

    # Vérifier la connexion au fichier source (test de disponibilité)
    max_retries = 3
    retry_delay = 10  # secondes entre chaque essai
    for _ in range(max_retries):
        if os.path.exists(src_path_str):
            break
        time.sleep(retry_delay)
    else:
        # Si après 3 essais, le fichier n'est toujours pas accessible
        QMessageBox.warning(
            None,
            "Erreur de connexion",
            "Le fichier source est inaccessible après plusieurs tentatives.\n"
            "Veuillez vérifier votre connexion réseau ou l'accès au fichier.\n"
            "Le plugin sera lancé sans mise à jour des données."
        )
        return False

    # Copier chaque fichier associé
    for ext in shapefile_extensions:
        src_file = src_path_str.replace('.shp', ext)
        if os.path.exists(src_file):
            dst_file = os.path.join(dst_dir, os.path.basename(src_file))
            try:
                shutil.copy2(src_file, dst_file)
                print(f"Copié : {src_file} -> {dst_file}")
            except OSError as e:
                QMessageBox.warning(
                    None,
                    "Erreur de copie",
                    f"Impossible de copier le fichier {src_file} vers {dst_file}.\n"
                    f"Erreur : {e}\n"
                    "Le plugin sera lancé sans mise à jour des données."
                )
                return False

    return True
    
def copy_shapefile_components_old(src_path, dst_dir):
    # Liste des extensions de fichiers associés à un shapefile
    shapefile_extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qml', '.sbn', '.sbx', '.fbn', '.fbx', '.ain', '.aih', '.ixs', '.mxs', '.atx', '.xml']

    # Convertir le Path en chaîne de caractères pour utiliser replace
    src_path_str = str(src_path)

    # Copier chaque fichier associé
    for ext in shapefile_extensions:
        src_file = src_path_str.replace('.shp', ext)
        if os.path.exists(src_file):
            dst_file = os.path.join(dst_dir, os.path.basename(src_file))
            shutil.copy2(src_file, dst_file)
            print(f"Copié : {src_file} -> {dst_file}")
            
            
def get_original_source_and_filter(layer_source):
    # Extraire le chemin du fichier original et les filtres
    if '|' in layer_source:
        original_source, filter_part = layer_source.split('|', 1)
        return unquote(original_source), '|' + filter_part
    return unquote(layer_source), ''

  
def createur_csv_rapport_layer(qgsproject, local_folder):
    project_name = (qgsproject.fileName().split('/')[-1]).split('.')[0]
    # Layers
    layers = qgsproject.mapLayers().values()
    layers_column_names = ['id',
                            'Type',
                            'name',
                            'storage',
                            'path',
                            'cree_le',
                            'date_MAJ'
                             ]
    layers_data = []
    nn= 1
    for index, layer in enumerate(layers, start=1):
        provider = layer.dataProvider()
        layer_index = index # ce sera l'id dans la liste
        if isinstance(layer, QgsVectorLayer): 
            TypeLayer = 'Vecteur'
            layer_storage = layer.dataProvider().storageType()
            
        else :  
            TypeLayer = 'Rasteur'
            layer.providerType()
            
        layer_name = layer.name()
        path_url = get_url(layer)
        date_creation= get_file_creation_time(path_url)
        date_MAJ=get_file_modification_time(path_url)
        layers_data.append(
                [layer_index,  TypeLayer, layer_name, path_url, layer_storage,date_creation,date_MAJ]) 
        
    # create_csv_file:
    file_name= 'rapport_couches_'+ project_name +'.csv'
    csv_file = os.path.join(local_folder, file_name)
    with open(csv_file, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(layers_column_names)
        writer.writerows(layers_data)


def createur_csv_rapport_project(qgsproject, local_folder):
    # code pris dans le plugin project_report, fichier QProjectReport.py author=Patricio Soriano. SIGdeletras.com, email=pasoiano@gmail.com
    # Project
    project_name = (qgsproject.fileName().split('/')[-1]).split('.')[0]
     
    project_column_names = ['title',
                                 'file_name',
                                 'file_path',
                                 'crs_project',
                                 'layers_count',
                                 'creation_date',
                                 'last_save_date'
                                 ]
    project_file_path = os.path.split(qgsproject.fileName())[0]
    project_file_name = os.path.split(qgsproject.fileName())[1]
    project_data = []
    project_data = [
        str(qgsproject.title()),
        project_file_name,
        project_file_path,
        f'{qgsproject.crs().authid()} {qgsproject.crs().description()}',
        qgsproject.count(),
        qgsproject.metadata().creationDateTime().date().toString("yyyy-MM-dd HH:mm:ss"), 
        qgsproject.lastSaveDateTime().date().toString("yyyy-MM-dd HH:mm:ss")
        ]
    
    # create_csv_file:
    file_name= 'rapport_projet_'+ project_name +'.csv'
    csv_file = os.path.join(local_folder, file_name)
    with open(csv_file, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=';',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(project_column_names)
        writer.writerow(project_data)
       
def read_csv_2(csv_path):
    layers_info = []
    with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file, delimiter=';')
        for row in csv_reader:
            layers_info.append(row)
    return layers_info

def write_csv(csv_path, layers_info, fieldnames):
    with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(layers_info)

def update_layers(csv_name, local_folder):
    csv_file = Path(local_folder) / csv_name
    counter = 0
    liste_layer = []
    layers_info_f = read_csv_2(csv_file)
    fieldnames = layers_info_f[0].keys()  # Get the fieldnames from the first row

    for layer_info in layers_info_f:
        layer_name = layer_info['name']
        server_path = Path(layer_info['storage'])  # Convertir en objet Path
        date_creation = layer_info['cree_le']
        date_old = layer_info['date_MAJ']

        local_path = Path(local_folder) / server_path.name
        server_mod_time = get_file_modification_time(server_path)
        local_mod_time = get_file_modification_time(local_path)

        # Décomposer la condition en plusieurs étapes
        if not server_mod_time:
            print(f"Server mod time is not available for layer: {layer_name}")
            continue

        if not local_mod_time:
            print(f"Local mod time is not available for layer: {layer_name}")
            copy_shapefile_components(server_path, local_folder)
            print(f"Updated layer (no local mod time): {layer_name}")
            counter += 1
            liste_layer.append(str(layer_name))
            layer_info['date_MAJ'] = get_file_modification_time(local_path)
            continue

        if server_mod_time > local_mod_time:
            copy_shapefile_components(server_path, local_folder)
            print(f"Updated layer (server mod time > local mod time): {layer_name}")
            counter += 1
            liste_layer.append(str(layer_name))
            layer_info['date_MAJ'] = get_file_modification_time(local_path)

        if server_mod_time > date_old:
            copy_shapefile_components(server_path, local_folder)
            print(f"Updated layer (server mod time > date_old): {layer_name}")
            counter += 1
            liste_layer.append(str(layer_name))
            layer_info['date_MAJ'] = get_file_modification_time(local_path)

    if counter == 0:
        QMessageBox.information(None, "information:", 'Pas de couches à mettre à jour !')
    elif counter == 1:
        write_csv(csv_file, layers_info_f, fieldnames)
        toto = "Le projet qgis local vient d'être mis à jour!\n"
        toto += 'Et une seule couche a été mise à jour depuis le serveur,\n'
        toto += "il s'agit de : \n"
        for c in liste_layer:
            toto += ' - ' + c + '\n'
        toto += "A présent, vous allez pouvoir utiliser l'outil"
        QMessageBox.information(None, "information:", toto)
    else:
        write_csv(csv_file, layers_info_f, fieldnames)
        toto = "Le projet qgis local vient d'être mis à jour!\n"
        toto += 'et ' + str(counter) + ' couches ont été mises à jour depuis le serveur,\n'
        toto += "il s'agit de : \n"
        for c in liste_layer:
            toto += ' - ' + c + '\n'
        toto += "A présent, vous allez pouvoir utiliser l'outil"
        QMessageBox.information(None, "information:", toto)
        
def get_layer_group(layer_tree, layer):
    # Obtenir le groupe auquel appartient une couche
    for node in layer_tree.findLayers():
        if node.layerId() == layer.id():
            parent = node.parent()
            if isinstance(parent, QgsLayerTreeGroup):
                return parent.name()
    return ''


def create_local_project_with_local_layers_2(nom_projet_maitre, original_project_path, local_layers_dir):
    # Vérifier si le fichier .qgz existe
    if not os.path.exists(original_project_path):
        print(f"Erreur : Le fichier {original_project_path} n'existe pas.")
        return None

    # Vérifier si le fichier .qgz est un fichier ZIP valide
    if not zipfile.is_zipfile(original_project_path):
        print(f"Erreur : Le fichier {original_project_path} n'est pas un fichier ZIP valide.")
        return None

    # Créer le répertoire de destination s'il n'existe pas
    os.makedirs(local_layers_dir, exist_ok=True)

    # Extraire le contenu du fichier .qgz
    try:
        with zipfile.ZipFile(original_project_path, 'r') as z:
            z.extractall(local_layers_dir)
    except zipfile.BadZipFile:
        print(f"Erreur : Le fichier {original_project_path} est corrompu ou n'est pas un fichier ZIP valide.")
        return None

    # Chemin du fichier .qgs extrait
    qgs_file_path = Path(local_layers_dir) / (Path(original_project_path).stem + '.qgs')

    # Lire le fichier .qgs
    tree = ET.parse(qgs_file_path)
    root = tree.getroot()

    # Répertoire racine du projet original
    original_project_root = Path(original_project_path).parent

    # Vérifier si le fichier CSV "rapport_couches" existe déjà dans le répertoire local
    csv_file_path = Path(local_layers_dir) / f"rapport_couches_{nom_projet_maitre}.csv"
    #csv_file = Path(local_folder) / csv_name
    existing_layers = []
    if csv_file_path.exists():
        layers_info_f = read_csv_2(csv_file_path)
        for dico in layers_info_f:
            nom=dico['name']
            existing_layers.append(nom)
            #existing_layers = [dico['name'] for dico in layers_info_f]
    nn=1
    # Mettre à jour les chemins des couches pour pointer vers les fichiers locaux
    for maplayer in root.findall(".//maplayer"):
        if maplayer.get('type') == 'vector':
            datasource = maplayer.find('datasource')
            if datasource is not None:
                src_file_rel, filter_part = get_original_source_and_filter(datasource.text)
                src_file_abs = Path(src_file_rel)
                layer_path = src_file_abs.resolve()

                if layer_path.suffix == '.shp':
                    layer_name = os.path.basename(layer_path)
                    local_layer_path = os.path.join(local_layers_dir, layer_name)
         
                    if layer_name in existing_layers:
                        existing_layers.remove(layer_name)
                    else:
                        datasource.text = f"{local_layer_path}{filter_part}"
                        # Copier tous les fichiers associés au shapefile
                        copy_shapefile_components(layer_path, local_layers_dir)
                elif layer_path.suffix == '.gpkg':
                    layer_name = os.path.basename(layer_path)
                    """
                    if nn<3:
                        nn=+1
                        QMessageBox.information(None,"information:", "Debug 1 de create_local_project_with_local_layers_2" + 
                            'layer_name: ' +str(layer_name))
                    """
                    local_layer_path = os.path.join(local_layers_dir, layer_name)
                    if layer_name in existing_layers:
                        existing_layers.remove(layer_name)
                    else:
                        datasource.text = f"{local_layer_path}{filter_part}"
                        # Copier le fichier GeoPackage
                        shutil.copy2(layer_path, local_layer_path)
                        print(f"Copié : {layer_path} -> {local_layer_path}")
                else:
                    layer_name = os.path.basename(layer_path)
                    local_layer_path = os.path.join(local_layers_dir, layer_name)
                    if layer_name in existing_layers:
                        existing_layers.remove(layer_name)
                    else:
                        datasource.text = f"{local_layer_path}{filter_part}"
                        # Copier le fichier de la couche
                        shutil.copy2(layer_path, local_layer_path)
                        print(f"Copié : {layer_path} -> {local_layer_path}")
        elif maplayer.get('type') == 'raster':
            datasource = maplayer.find('datasource')
            if datasource is not None:
                layer_source, filter_part = get_original_source_and_filter(datasource.text)
                if 'url=' in layer_source or 'SERVICE=WMTS' in layer_source or 'SERVICE=WMS' in layer_source:
                    # C'est probablement un flux WMS ou WMTS
                    # Ignorer la copie pour ces couches
                    print(f"Flux WMS/WMTS détecté, ignoré pour la copie locale : {layer_source}")
                else:
                    layer_path = Path(layer_source).resolve()
                    layer_name = os.path.basename(layer_path)
                    local_layer_path = os.path.join(local_layers_dir, layer_name)
                    if layer_name in existing_layers:
                        existing_layers.remove(layer_name)
                    else:
                        datasource.text = f"{local_layer_path}{filter_part}"
                        # Copier le fichier de la couche
                        shutil.copy2(layer_path, local_layer_path)
                        print(f"Copié : {layer_path} -> {local_layer_path}")

    # Enregistrer les modifications dans le fichier .qgs
    tree.write(qgs_file_path, encoding='utf-8', xml_declaration=True)

    # Définir le chemin de sortie du projet avec le postfixe '_local'
    project_local_name = f"{nom_projet_maitre}_local.qgz"
    output_project_path = os.path.join(local_layers_dir, project_local_name)

    # Créer un nouveau fichier .qgz avec les modifications
    with zipfile.ZipFile(output_project_path, 'w') as z:
        # Ajouter uniquement le fichier .qgs modifié
        z.write(qgs_file_path, arcname=qgs_file_path.name)
    
    # Supprimer les couches restantes dans le répertoire local
    #QMessageBox.information(None,"information:", "Debug 1 de create_local_project_with_local_layers_2" + 'liste existing_layers: ' +str(existing_layers))
    for layer_name in existing_layers:
        local_layer_path = Path(local_layers_dir) / layer_name
        if local_layer_path.exists():
            shutil.rmtree(local_layer_path.parent)
    
    print(f"Nouveau projet enregistré à : {output_project_path}")
    return output_project_path

def verif_update_project(projet_maitre_url, projet_maitre_name, local_layers_dir):

    # Lire le fichier CSV du projet local
    csv_file_path = Path(local_layers_dir) / f"rapport_projet_{projet_maitre_name}.csv"
    if not csv_file_path.exists():
        print(f"Erreur : Le fichier CSV {csv_file_path} n'existe pas.")
        return

    # Lire les informations du projet local
    project_info = read_csv_2(csv_file_path)[0]
    local_creation_date = project_info['creation_date']
    local_last_save_date = project_info['last_save_date']

    # Lire les informations du projet maître
    maitre_project = QgsProject()
    maitre_project.read(projet_maitre_url)
    maitre_creation_date = maitre_project.metadata().creationDateTime().date().toString("yyyy-MM-dd HH:mm:ss") # "yyyy-MM-dd" 
    maitre_last_save_date = maitre_project.lastSaveDateTime().date().toString("yyyy-MM-dd HH:mm:ss")

    # Comparer les dates de création et de dernière modification
    if local_creation_date != maitre_creation_date or local_last_save_date != maitre_last_save_date:
        print("Les dates de création ou de dernière modification diffèrent. Mise à jour du projet local.")
        # Mettre à jour le projet local
        create_local_project_with_local_layers_2(Path(projet_maitre_url).stem, projet_maitre_url, local_layers_dir)
        # Mettre à jour les fichiers de rapport
        createur_csv_rapport_layer(maitre_project, local_layers_dir)
        createur_csv_rapport_project(maitre_project, local_layers_dir)
    else:
        print("Les dates de création et de dernière modification sont identiques. Aucune mise à jour nécessaire.")

def check_and_update_last_verif_date(local_folder):
  
    # Chemin du fichier CSV
    csv_path = os.path.join(local_folder, 'date_derniere_verif.csv')

    # Obtenir la date actuelle
    current_date = datetime.now()
    current_day = current_date.strftime('%Y-%m-%d')

    # Vérifier si le fichier CSV existe
    if not os.path.exists(csv_path):
        # Si le fichier n'existe pas, le créer et écrire la date actuelle
        with open(csv_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['date'])
            writer.writerow([current_day])
        last_day = current_day  # Aucune date précédente à comparer
    else:
        # Si le fichier existe, lire la date sauvegardée
        with open(csv_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Sauter l'en-tête
            last_day = next(reader)[0]  # Lire la date sauvegardée

        # Comparer la date actuelle avec la date sauvegardée
        if current_day != last_day:
            # Mettre à jour le fichier avec la nouvelle date
            with open(csv_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['date'])
                writer.writerow([current_day])

    return current_day,last_day
