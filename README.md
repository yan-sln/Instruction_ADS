# Instruction_ADS
plugin d'interrogation de couches et de production d'exports cartographiques

Ce plugin est conçu pour les agents du service de la DDT de l'Instruction du Droit des Sols (ADS) souhaitant disposer dans Qgis_3, d'une fonctionnalité permettant, à partir d'une parcelle cadastrale localisée donnée, d'extraire de l'ensemble des couches contenues dans le projet QGIS (comme: couches des servitudes,natrura 2000, des aléas,..etc..),celles de ces couches qui intersectent la parcelle choisie.
Pour la ou les parcelle(s) choisie(s) le plugin produit une rapport pdf avec la liste des couches concernées, ainsi qu'un geopdf avec des 'vues' des couches concernées.

Pour fonctionner le projet doit contenir à minima les couches 'cadastrales' nommées ici 'N_COMMUNE_BDP_021','N_DIVCAD_BDP_021' et 'N_PARCELLE_BDP_021' qui doivent être spécifiées ligne 71 du script dlgbox_IADS.py !                                                                                                                                   
On veillera à adapter aussi les lignes du code de dlgbox_IADS.py partout où les attributs de ces couches sont utilisés en précisant les noms de ceux-ci.
Les couches de zonages à interroger sont rangées dans des groupes spécifiques qui doivent aussi être listés dans le corps du script juste après la définition des couches!                                                                                                                
Cette extension ne fait pas partie du moteur de Qgis. Toute demande est à adresser à l'auteur : Jean-Christophe Baudin
ddt-mpit-adl@cote-dor.gouv.fr ou jeanchristophebaudin@ymail.com
DDT21 SUCAT/BGAT
