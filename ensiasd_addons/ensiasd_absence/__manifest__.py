# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Gestion des Absences',
    'version': '17.0.2.0.0',
    'category': 'Education',
    'summary': 'Gestion avancée des absences avec formulaires web et notifications',
    'description': """
ENSIASD - Gestion des Absences v2.0
===================================

**Fonctionnalités principales :**
- Enregistrement et suivi des absences
- Formulaire d'appel en ligne envoyé par email aux enseignants
- Système de justification avec upload de documents
- Notifications automatiques aux étudiants
- Statistiques et tableaux de bord
- Intégration avec les séances et l'emploi du temps

**Nouveautés v2.0 :**
- Formulaire d'appel web accessible via token
- Envoi automatique d'emails aux enseignants
- Formulaire de justification en ligne pour les étudiants
- Workflow de validation des justifications
- Statistiques avancées par étudiant, module, groupe
- Export des données
    """,
    'author': 'ENSIASD',
    'website': 'https://ensiasd.ma',
    'license': 'LGPL-3',
    'depends': [
        'ensiasd_core',
        'ensiasd_student',
        'ensiasd_academic',
        'mail',
        'website',
    ],
    'data': [
        # Security - MUST be first
        'security/ir.model.access.csv',

        # Data
        'data/absence_data.xml',

        # Views - Load regular views first
        'views/ensiasd_absence_views.xml',
        'views/absence_templates.xml',

        # Wizards - MUST be loaded BEFORE menus that reference them
        'views/appel_wizard_views.xml',

        # Menus - Load LAST so all referenced actions exist
        'views/ensiasd_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 6,
}