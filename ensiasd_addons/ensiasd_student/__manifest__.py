# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Étudiants',
    'version': '17.0.2.0.0',
    'category': 'Education',
    'summary': 'Gestion complète des étudiants et inscriptions ENSIASD',
    'description': """
        Application de gestion des étudiants pour ENSIASD.

        Fonctionnalités:
        - Fiche étudiant complète (CNE, CIN, photo)
        - Inscription automatique à la filière
        - Inscription automatique aux modules de 1ère année
        - Affectation aux groupes
        - Historique du parcours académique
        - Intégration avec le module Contacts d'Odoo
    """,
    'author': 'ENSIASD - Jammi Osama',
    'website': 'https://ensiasd.ac.ma',
    'license': 'LGPL-3',

    'depends': [
        'ensiasd_core',
        'ensiasd_academic',
        'contacts',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/ensiasd_student_views.xml',
        'views/ensiasd_groupe_views.xml',
        'views/ensiasd_inscription_views.xml',
        'views/ensiasd_menu.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 2,
}