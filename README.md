# ENSIASD ERP - Système de Gestion Intégré

Système ERP complet développé pour l'**École Nationale Supérieure de l'Intelligence Artificielle et Sciences des Données (ENSIASD)** utilisant Odoo 17.

## 📋 Aperçu du Projet

Ce projet fournit une solution ERP modulaire pour la gestion académique complète incluant :

- **Gestion des étudiants** : Enregistrement des étudiants avec identifiants CNE/CIN
- **Programmes académiques** : Structure des programmes et planification des cours
- **Gestion des notes** : Enregistrement et gestion des résultats académiques
- **Suivi des absences** : Système de suivi de l'assiduité
- **Gestion des stages** : Gestion des internships et stages professionnels
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

7. **ensiasd_reports** - Rapports analytiques
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

### 1. Cloner le Repository

```bash
https://github.com/osama-jammi/ENSIASD-ERP---Syst-me-de-Gestion-Int-gr-.git
cd ensiasd-erp
```

### 2. Configuration de la Base de Données PostgreSQL

```bash
# Créer l'utilisateur PostgreSQL
createuser -U postgres openpg -P

# Créer la base de données
createdb -U postgres -O openpg ensiasd_v20
```

### 3. Configuration d'Odoo

Créer ou modifier le fichier `odoo.conf` :

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
addons_path = ./addons,./ensiasd_addons
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

### 4. Initialiser la Base de Données

**Première initialisation - Installation complète :**

```bash
python ./odoo/odoo-bin -c ./odoo/odoo.conf -i base -d ensiasd_v20 --without-demo=all
```

**Après installation initiale - Démarrage normal :**

```bash
python ./odoo/odoo-bin -c ./odoo/odoo.conf -d ensiasd_v20
```

### 5. Installation des Modules ENSIASD

Une fois Odoo en cours d'exécution, accédez à l'interface web à `http://localhost:8089`

1. Allez à **Tableau de Bord** → **Apps**
2. Cliquez sur **Mettre à jour la liste des apps**
3. Recherchez les modules ENSIASD :
   - ensiasd_core
   - ensiasd_student
   - ensiasd_academic
   - ensiasd_grades
   - ensiasd_absence
   - ensiasd_stage
   - ensiasd_reports

4. Cliquez **Installer** pour chaque module

## 🚀 Utilisation

### Démarrer le Serveur

```bash
# Mode développement
python ./odoo/odoo-bin -c ./odoo/odoo.conf -d ensiasd_v20

# Accéder à l'interface
# http://localhost:8089
```

### Accès Initial

- **URL** : http://localhost:8089
- **Utilisateur** : admin
- **Mot de passe** : admin

## 📁 Structure du Repository

```
ensiasd-erp/
├── README.md                 # Ce fichier
├── INSTALLATION.md           # Guide d'installation détaillé
├── .gitignore               # Fichier Git ignore
├── odoo.conf.template       # Template de configuration Odoo
│
├── ensiasd_addons/          # Modules ENSIASD
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
│   └── ensiasd_reports/
│
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   └── API.md
│
├── scripts/                 # Scripts utilitaires
│   ├── init_db.sh
│   ├── backup_db.sh
│   └── restore_db.sh
│
└── tests/                   # Tests unitaires
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
https://github.com/osama-jammi/ENSIASD-ERP---Syst-me-de-Gestion-Int-gr-.git
# Ajouter tous les fichiers
git add .

# Premier commit
git commit -m "Initial commit: ENSIASD ERP base avec 7 modules"

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
git commit -m "feat: ajouter validation des absences"

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
    └→ ensiasd_stage (dépend de student)
    
ensiasd_reports (dépend de tous)
```

 

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

## 👤 Auteur

**Osama** - Développement ERP/Odoo

## 📞 Support

Pour les problèmes ou questions :
- Ouvrir une **Issue** sur GitHub
- Vérifier la **Documentation**
- Consulter les **Discussions**

## 🔗 Ressources Utiles

- [Documentation Odoo 17](https://www.odoo.com/documentation/17.0/)
- [Développement Modules Odoo](https://www.odoo.com/documentation/17.0/developer/reference.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python Documentation](https://docs.python.org/3/)

---

**Dernière mise à jour** : 2025-12-09
**Version** : 1.0.0
