# Dissection du plugin Instruction_ADS

## Ce que fait le plugin

**Instruction_ADS** est un plugin QGIS conçu pour les agents DDT (Direction Départementale des Territoires) qui instruisent les autorisations d'urbanisme (droit des sols).

Workflow :
1. L'utilisateur sélectionne une **parcelle cadastrale** (commune → section → parcelle)
2. Le plugin **intersecte toutes les couches du projet** (zones inondables, biodiversité, patrimoine, urbanisme, etc.) avec cette parcelle
3. Il génère des **rapports** (PDF, GeoPDF, CSV, ODS) et des **cartes thématiques** listant chaque zone réglementaire qui concerne la parcelle

## Structure des fichiers

| Fichier | Rôle |
|---------|------|
| `__init__.py` | Point d'entrée QGIS |
| `Instruction_ADS.py` | Shell du plugin (toolbar, menu, rechargement à chaud) |
| `dlgBox_IADS.py` | **Le gros morceau** — UI + logique métier (sélection parcelle, intersection, résultats) |
| `doDlgBox_IADS.py` | Wrapper QDialog pour `dlgBox_IADS` |
| `fonctions_lnstruction_ADS.py` | Fonctions d'export (PDF, GeoPDF, CSV, cartes) — NB: typo dans le nom (`ln` au lieu de `In`) |
| `project_updater.py` | Sync réseau (non utilisé, voir ci-dessous) |
| `odswriter/` | Bibliothèque embarquée pour l'export ODS |
| `about_IADS.py` / `doAbout_IADS.py` | Dialogue "À propos" |

## Ce qu'on a changé

### 1. Suppression du mécanisme de synchronisation réseau

Le plugin original copie un projet QGIS "maître" (~20 Go) depuis un lecteur réseau `W:/` vers un dossier local `projet_local/`, avec vérification quotidienne des mises à jour.

**Supprimé** : tout le bloc de sync (~150 lignes) dans `dlgBox_IADS.py`. Remplacé par :
```python
project_local_path = QgsProject.instance().fileName()
```
Le plugin utilise maintenant le projet/les couches déjà ouverts dans QGIS.

Imports supprimés : `project_updater`, `zipfile`, `xml.etree.ElementTree`.

### 2. Correction de `from console import *`

Dans `Instruction_ADS.py` : import supprimé (crashait au chargement hors console Python QGIS). N'était utilisé que dans du code commenté.

### 3. Rechargement à chaud

`LoadDlgBoxQt1()` dans `Instruction_ADS.py` fait maintenant un `importlib.reload()` de `dlgBox_IADS` et `doDlgBox_IADS` à chaque clic. Plus besoin de redémarrer QGIS pour tester des modifications.

### 4. Adaptation aux couches PCI Express standard

Noms des couches cadastrales mis à jour :
- `N_COMMUNE_PCIe_021` → `COMMUNE`
- `N_FEUILLE_PCIe_021` → `FEUILLE`
- `N_PARCELLE_PCIe_021` → `PARCELLE`

Accès aux attributs par index (`feat_parcelle[4]`) remplacés par accès par nom (`feat_parcelle['NOM_COM']`), pour fonctionner avec n'importe quel PCI Express départemental.

### 5. Gestion des groupes manquants

Le code original crashait (`AttributeError: 'NoneType'`) dès qu'un groupe attendu n'existait pas dans le panneau Couches. Tous les appels `root.findGroup(nom_groupe)` sont maintenant protégés par un test `if groupe is None: continue`.

Endroits corrigés :
- `doInterrogation()` : collecte des couches à interroger
- `Exports()` : extinction/allumage des couches pour la production de cartes (5 occurrences)
- `doInterrogation()` : suppression de la couche rapport du groupe CADASTRE

### 6. Gestion du groupe CADASTRE manquant

Le code essayait de retirer les couches rapport d'un groupe `CADASTRE` (qui n'existe pas dans notre configuration). Ajout d'un guard `if group_cadastre is not None`.

## Comment faire tourner le plugin

### Prérequis

- QGIS 3.x
- Plugin Reloader (optionnel mais recommandé pour le dev)

### Installation

```bash
# Symlink du repo dans le dossier plugins QGIS (macOS)
ln -s /chemin/vers/Instruction_ADS \
  ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/Instruction_ADS
```

Sous Linux :
```bash
ln -s /chemin/vers/Instruction_ADS \
  ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/Instruction_ADS
```

Puis dans QGIS : **Extensions → Gérer/Installer → chercher "Instruction_ADS" → activer**.

### Données cadastrales

Télécharger le Parcellaire Express (PCI) pour le département voulu :
```
https://data.geopf.fr/telechargement/download/PARCELLAIRE-EXPRESS/PARCELLAIRE-EXPRESS_1-1__SHP_LAMB93_D0XX_2025-12-01/PARCELLAIRE-EXPRESS_1-1__SHP_LAMB93_D0XX_2025-12-01.7z
```
(remplacer `XX` par le numéro de département)

Extraire l'archive, puis charger dans QGIS les trois shapefiles depuis le dossier `1_DONNEES_LIVRAISON_.../PEPCI_1-1_SHP_LAMB93_D0XX/` :
- **COMMUNE.SHP**
- **FEUILLE.SHP**
- **PARCELLE.SHP**

Les noms des couches dans le panneau Couches doivent être exactement `COMMUNE`, `FEUILLE`, `PARCELLE`.

### Couches à interroger (les groupes)

Le moteur d'intersection ne requête **que** les couches vectorielles placées dans des **groupes nommés** spécifiques du panneau Couches. Les couches hors de ces groupes sont ignorées.

Les noms de groupes attendus sont définis dans `dlgBox_IADS.py` :
```python
Liste_des_groupes_a_interroger = [
    'Eau', 'Autres SUP', 'Urbanisme', 'Nuisances',
    'Risques naturels', 'Biodiversité', 'Patrimoine',
    'Risques technologiques', 'Agriculture',
    'Specifiques projets photovoltaïques'
]
```

**Les groupes absents sont silencieusement ignorés** — il n'est pas nécessaire de tous les créer.

Pour ajouter des couches à interroger :
1. Clic droit dans le panneau Couches → **Ajouter un groupe**
2. Nommer le groupe **exactement** comme l'un des noms ci-dessus (attention aux accents et à la casse)
3. Glisser les couches vectorielles voulues **dans** ce groupe
4. Les couches doivent avoir des géométries qui recouvrent la zone des parcelles testées

On peut aussi modifier la liste `Liste_des_groupes_a_interroger` dans `dlgBox_IADS.py` pour ajouter ses propres noms de groupes.

**Important** : les groupes ne doivent pas contenir de sous-groupes (limitation du code actuel).

### Sélection de parcelle alternative

En plus des menus déroulants (commune → section → parcelle), on peut sélectionner une parcelle directement sur la carte :
1. Rendre la couche `PARCELLE` active dans le panneau Couches
2. Utiliser l'outil de sélection QGIS (icône curseur jaune, ou touche **S**)
3. Cliquer sur une parcelle sur la carte
4. Cliquer "Interroger les données" dans le plugin

Le moteur travaille sur `Couche_Parcelle.selectedFeatures()`, donc toute méthode de sélection fonctionne.

### Utilisation

1. Cliquer sur le bouton du plugin dans la toolbar
2. Sélectionner une commune dans la liste déroulante
3. Sélectionner une section, puis une parcelle
4. Cliquer **"Interroger les données"** — crée des couches rapport dans un groupe "Rapports"
5. Choisir un dossier d'export
6. Cliquer **"Générer les exports et les cartes"** — produit SHP, ODS, PDF, GeoPDF dans le dossier choisi

## Problèmes connus restants

- **Performance** : le chargement des parcelles d'une section est lent sur les gros départements (ex: 59 Nord). Pas de filtre spatial, toutes les parcelles sont itérées.
- **Rasters manquants** : les exports cartographiques référencent des rasters hard-codés (`N_ORTHO_COUL_2017_021`, `n_scan25_tour_021`) qui n'existent pas dans notre configuration. Les cartes avec fond Scan25 ou Orthophoto ne fonctionneront pas.
- **Typo dans le nom de fichier** : `fonctions_lnstruction_ADS.py` (l minuscule au lieu de I majuscule).
- **Variables non définies** dans `fonctions_lnstruction_ADS.py` : `message` (ligne 79), `Dico_resultat` (ligne 89) — fonctions probablement inutilisées.
- **Globales** : le code utilise massivement `global`, ce qui rend le debug difficile.
