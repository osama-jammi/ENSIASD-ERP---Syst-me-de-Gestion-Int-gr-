# ENSIASD ERP - Système de Gestion Intégré

Système ERP complet développé pour l'École Nationale Supérieure de l'Intelligence Artificielle et Sciences des Données (ENSIASD) utilisant Odoo 17.

## 📋 Aperçu du Projet

Ce projet fournit une solution ERP modulaire pour la gestion académique complète incluant :

- **Gestion des étudiants** : Enregistrement des étudiants avec identifiants CNE/CIN
- **Programmes académiques** : Structure des programmes et planification des cours
- **Gestion des notes** : Enregistrement et gestion des résultats académiques
- **Suivi des absences** : Système de suivi de l'assiduité
- **Gestion des stages** : Gestion des internships et stages professionnels
- **Emplois du temps** : Gestion et planification des emplois du temps
- **Rapports académiques** : Génération de rapports analytiques
- **Configuration de base** : Gestion des années académiques et des salles

## 🏗️ Architecture Modulaire

### Modules Développés

1. **ensiasd_core** - Base configuration
   - Années académiques
   - Salles/Locaux
   - Configuration générale du système

2. **ensiasd_student** - Gestion des étudiants
   - Enregistrement des étudiants
   - Identifiants CNE/CIN
   - Données personnelles

3. **ensiasd_academic** - Programmes académiques
   - Programmes d'études
   - Cours et planification
   - Calendrier académique

4. **ensiasd_grades** - Gestion des notes
   - Enregistrement des notes
   - Calcul des moyennes
   - Transcripts académiques

5. **ensiasd_absence** - Suivi de l'assiduité
   - Enregistrement des absences
   - Rapports d'assiduité
   - Statistiques d'attendance

6. **ensiasd_stage** - Gestion des stages
   - Enregistrement des stages
   - Suivi des internships
   - Évaluation des stages

7. **ensiasd_timetable** - Gestion des emplois du temps
   - Planification des cours
   - Génération des horaires
   - Gestion des salles et ressources
   - Détection des conflits d'emploi du temps
   - Export PDF/Excel des emplois du temps

8. **ensiasd_reports** - Rapports analytiques
   - Rapports académiques
   - Statistiques d'étudiants
   - Tableaux de bord

## 🔧 Prérequis Système

- **Odoo** : Version 17.0
- **Python** : 3.10, 3.11 ou 3.12
- **PostgreSQL** : 12 ou supérieur
- **Système** : Windows, Linux ou macOS
- **Node.js** : 14+ (pour les assets front-end)

## 📦 Installation et Configuration

### 1. Préparation de l'Environnement

```bash
# Créer un répertoire pour le projet
mkdir ensiasd-project
cd ensiasd-project

# Créer un répertoire pour Odoo
mkdir odoo
```

### 2. Cloner le Repository ENSIASD ERP

```bash
# Cloner le repository ENSIASD ERP
git clone https://github.com/osama-jammi/ENSIASD-ERP---Syst-me-de-Gestion-Int-gr-.git ensiasd-erp
cd ensiasd-erp
```

### 3. Cloner Odoo 17

```bash
# Se déplacer dans le dossier odoo
cd ../odoo

# Cloner Odoo 17 depuis la source officielle
git clone https://github.com/odoo/odoo.git --branch 17.0 --depth 1 .

# Installer les dépendances Python d'Odoo
pip install -r requirements.txt

# Retourner au répertoire ensiasd-erp
cd ../ensiasd-erp
```

### 4. Configuration de la Base de Données PostgreSQL

```bash
# Créer l'utilisateur PostgreSQL
sudo -u postgres createuser -U postgres openpg -P

# Créer la base de données
sudo -u postgres createdb -U postgres -O openpg ensiasd_v20
```

**Note pour Windows :**
- Utiliser pgAdmin ou les commandes via PostgreSQL Shell

### 5. Configuration d'Odoo

Créer ou modifier le fichier `odoo.conf` dans le répertoire principal :

```ini
[options]
; Généralités
admin_passwd = admin
db_host = localhost
db_port = 5432
db_user = openpg
db_password = mot_de_passe
db_name = ensiasd_v20

; Répertoires
addons_path = ../odoo/addons,./ensiasd_addons
data_dir = ./data

; Port
http_port = 8089
http_interface = 0.0.0.0

; Logs
log_level = info
log_file = ./logs/odoo.log
logfile = ./logs/odoo.log

; Mode développeur
dev_mode = True
```

### 6. Initialiser la Base de Données

**Première initialisation - Installation complète :**

```bash
# Depuis le répertoire ensiasd-erp
python ../odoo/odoo-bin -c odoo.conf -i base -d ensiasd_v20 --without-demo=all
```

**Après installation initiale - Démarrage normal :**

```bash
python ../odoo/odoo-bin -c odoo.conf -d ensiasd_v20
```

### 7. Installation des Modules ENSIASD

Une fois Odoo en cours d'exécution, accédez à l'interface web à `http://localhost:8089`

1. Allez à **Tableau de Bord → Apps**
2. Cliquez sur **Mettre à jour la liste des apps**
3. Recherchez les modules ENSIASD :
   - ensiasd_core
   - ensiasd_student
   - ensiasd_academic
   - ensiasd_grades
   - ensiasd_absence
   - ensiasd_stage
   - ensiasd_timetable
   - ensiasd_reports
4. Cliquez **Installer** pour chaque module dans l'ordre de dépendance

## 🚀 Utilisation

### Démarrer le Serveur

```bash
# Depuis le répertoire ensiasd-erp
python ../odoo/odoo-bin -c odoo.conf -d ensiasd_v20

# Accéder à l'interface
# http://localhost:8089
```

### Accès Initial

- **URL** : http://localhost:8089
- **Utilisateur** : admin
- **Mot de passe** : admin

## 📁 Structure du Repository

```
ensiasd-project/
├── odoo/                    # Code source Odoo 17 (cloné)
│   ├── odoo-bin
│   ├── addons/
│   ├── requirements.txt
│   └── ...
│
└── ensiasd-erp/            # Projet ENSIASD ERP
    ├── README.md           # Ce fichier
    ├── INSTALLATION.md     # Guide d'installation détaillé
    ├── .gitignore         # Fichier Git ignore
    ├── odoo.conf          # Configuration Odoo
    │
    ├── ensiasd_addons/    # Modules ENSIASD
    │   ├── ensiasd_core/
    │   │   ├── __manifest__.py
    │   │   ├── __init__.py
    │   │   ├── models/
    │   │   ├── views/
    │   │   ├── data/
    │   │   └── security/
    │   │
    │   ├── ensiasd_student/
    │   ├── ensiasd_academic/
    │   ├── ensiasd_grades/
    │   ├── ensiasd_absence/
    │   ├── ensiasd_stage/
    │   ├── ensiasd_timetable/   # Module emplois du temps
    │   └── ensiasd_reports/
    │
    ├── docs/              # Documentation
    │   ├── ARCHITECTURE.md
    │   ├── DATABASE_SCHEMA.md
    │   └── API.md
    │
    ├── scripts/           # Scripts utilitaires
    │   ├── init_db.sh
    │   ├── backup_db.sh
    │   └── restore_db.sh
    │
    └── tests/             # Tests unitaires
        ├── test_student.py
        ├── test_grades.py
        └── test_academic.py
```

## 🔄 Flux de Travail Git

### Initialiser un Repository Local

```bash
# Initialiser Git
git init

# Ajouter la remote
git remote add origin https://github.com/osama-jammi/ENSIASD-ERP---Syst-me-de-Gestion-Int-gr-.git

# Ajouter tous les fichiers
git add .

# Premier commit
git commit -m "Initial commit: ENSIASD ERP base avec 8 modules"

# Pousser vers GitHub
git branch -M main
git push -u origin main
```

### Commits Réguliers

```bash
# Voir le status
git status

# Ajouter les modifications
git add .

# Commit avec message descriptif
git commit -m "feat(timetable): ajouter gestion des emplois du temps"

# Pousser vers GitHub
git push origin main
```

## 📊 Dépendances Entre Modules

```
ensiasd_core (base)
    ↓
ensiasd_student (dépend de core)
    ↓
ensiasd_academic (dépend de student)
    ├→ ensiasd_grades (dépend de academic)
    ├→ ensiasd_absence (dépend de academic)
    ├→ ensiasd_timetable (dépend de academic et student)
    └→ ensiasd_stage (dépend de student)
    
ensiasd_reports (dépend de tous)
```

## 🕒 Module Timetable

Le module **ensiasd_timetable** comprend :

### Fonctionnalités principales :

- **Planification des cours** : Création automatique et manuelle des horaires
- **Gestion des salles** : Allocation optimale des salles de classe
- **Gestion des enseignants** : Assignation des professeurs aux créneaux
- **Vérification des conflits** : Détection automatique des chevauchements
- **Export des emplois du temps** : Formats PDF, Excel, et calendrier numérique
- **Notifications** : Alertes pour les changements d'horaires

### Dépendances :

- **ensiasd_academic** : Pour les cours et programmes
- **ensiasd_student** : Pour les groupes d'étudiants
- **ensiasd_core** : Pour les salles et ressources

## 📝 Conventions de Code

- **Python** : PEP 8
- **Modules** : Suivre la structure Odoo standard
- **Nommage** : snake_case pour les fonctions et variables
- **Documentation** : Docstrings en français et anglais
- **Tests** : Couvrir au minimum 80% du code

## 🤝 Contribution

Les contributions sont bienvenues. Veuillez :

1. Créer une branche pour votre feature : `git checkout -b feature/ma-feature`
2. Commiter vos changements : `git commit -m "feat: description"`
3. Pousser vers la branche : `git push origin feature/ma-feature`
4. Ouvrir une Pull Request

## 📄 Licence

Ce projet est développé pour ENSIASD. Licencié sous MIT License.

## 📞 Support

Pour les problèmes ou questions :

- Ouvrir une Issue sur GitHub
- Vérifier la Documentation
- Consulter les Discussions

## 🔗 Ressources Utiles

- [Documentation Odoo 17](https://www.odoo.com/documentation/17.0/)
- [Développement Modules Odoo](https://www.odoo.com/documentation/17.0/developer.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python Documentation](https://docs.python.org/3/)

---

**Dernière mise à jour** : 2025-12-17  
**Version** : 1.2.0 (avec module Timetable)  
**Statut** : Production Ready
