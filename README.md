# Fusion de plusieurs PDF en un seul document de plusieurs pages au format paysage A5

Le script est applicable pour créer un carnet de partitions du musique.

## ⚠️ Prérequis important

Le projet est configuré de sorte qu'il soit utilisé sur une plateforme datalab Onyxia (SSPCloud ou LS3). En particulier, avant tout lancement de programme, il est nécessaire de disposer dans son bucket MinIO d'un dossier nommé `carnet_partitions`, avec à l'intérieur les fichiers PDF à fusionner (dans un dossier nommé `partitions`), la page de garde nommé `page_garde.pdf` et le fichier CSV `list.csv`.

```plaintext
bucket/
└── carnet_partitions/
    └── partitions/
        └── 001.pdf
        └── 002.pdf
        ...
    └── page_garde.pdf
    └── liste.csv
```

## Création du service sur Onixya 

1. Créez un nouveau service Python sur Onixya
2. Ajouter l'URL du repository dans les paramètres : https://github.com/thomasguinhut/carnet_partitions
3. Lancer et ouvrir le dossier parent du projet

## Lancement du programme**

```bash
pip install -r requirements.txt
```

```bash
python main.py 
```