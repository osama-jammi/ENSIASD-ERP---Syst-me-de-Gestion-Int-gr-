# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Emploi du Temps',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Génération automatique des emplois du temps et planification des séances',
    'description': """
ENSIASD - Gestion des Emplois du Temps
======================================

**Fonctionnalités principales :**
- Définition des créneaux horaires disponibles
- Configuration des contraintes (salles, enseignants, groupes)
- Génération automatique des emplois du temps par filière/semestre
- Planification automatique des séances à partir de l'emploi du temps
- Vue calendrier interactive
- Gestion des conflits et indisponibilités
- Export PDF de l'emploi du temps

**Automatisation :**
- Création automatique des séances pour la période choisie
- Respect des volumes horaires des éléments
- Vérification des disponibilités
- Notifications aux enseignants
    """,
    'author': 'ENSIASD',
    'website': 'https://ensiasd.ma',
    'license': 'LGPL-3',
    'depends': [
        'ensiasd_core',
        'ensiasd_student',
        'ensiasd_academic',
        'mail',
    ],
    'data': [
        # Security
        'security/timetable_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/creneau_data.xml',
        'data/cron_data.xml',
        # Views - Load in correct order
        'views/ensiasd_creneau_views.xml',
        'views/ensiasd_emploi_views.xml',
        'views/ensiasd_emploi_ligne_views.xml',
        'views/ensiasd_indisponibilite_views.xml',
        'views/ensiasd_seance_extend_views.xml',
        # Wizards - Load BEFORE menus that reference them
        'wizard/generate_timetable_wizard_views.xml',
        'wizard/generate_seances_wizard_views.xml',
        # Menus - Load LAST
        'views/ensiasd_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 5,
}