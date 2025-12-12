# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Notes & Évaluations',
    'version': '17.0.2.0.1',
    'category': 'Education',
    'summary': 'Gestion complète des notes, moyennes, délibérations et bulletins',
    'description': """
ENSIASD - Module de Gestion des Notes v2.0.1
============================================

Ce module offre une gestion complète du système de notation :

**Fonctionnalités principales :**
- Saisie des notes par type d'évaluation (CC, Examen, TP, Projet, Rattrapage)
- Calcul automatique des moyennes (par élément, module, semestre, année)
- Gestion des sessions (Normale et Rattrapage)
- Système de délibération avec workflow
- Génération de bulletins de notes PDF
- Statistiques et tableaux de bord
- Import/Export des notes (Excel)
- Historique et traçabilité complète

**Corrections v2.0.1 :**
- Correction des droits d'accès
- Correction des groupes de sécurité
- Amélioration de l'affichage des menus
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
        # Security - DOIT être en premier
        'security/grades_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        'data/grades_data.xml',
        # Views
        'views/ensiasd_session_views.xml',
        'views/ensiasd_bareme_views.xml',
        'views/ensiasd_note_element_views.xml',
        'views/ensiasd_note_views.xml',
        'views/ensiasd_resultat_views.xml',
        'views/ensiasd_deliberation_views.xml',
        'views/ensiasd_bulletin_views.xml',
        'views/dashboard_views.xml',
        'views/ensiasd_menu.xml',
        # Wizards
        'wizard/note_import_wizard_views.xml',
        'wizard/note_saisie_wizard_views.xml',
        'wizard/deliberation_wizard_views.xml',
        # Reports
        'reports/report_bulletin.xml',
        'reports/report_releve_notes.xml',
        'reports/report_pv_deliberation.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ensiasd_grades/static/src/css/grades_dashboard.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 4,
}
