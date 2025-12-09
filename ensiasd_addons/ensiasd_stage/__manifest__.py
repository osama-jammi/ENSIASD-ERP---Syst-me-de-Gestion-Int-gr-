# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Stages',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Gestion des stages et PFE',
    'description': """
        Application de gestion des stages pour ENSIASD.
        - Entreprises partenaires (intégration avec Contacts Odoo)
        - Conventions de stage
        - Encadrement et soutenances
    """,
    'author': 'ENSIASD - Jammi Osama',
    'license': 'LGPL-3',
    'depends': [
        'ensiasd_core',
        'ensiasd_student',
        'contacts',  # Intégration avec Contacts pour les entreprises
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/ensiasd_stage_views.xml',
        'views/ensiasd_entreprise_views.xml',
        'views/ensiasd_menu.xml',
    ],
    'installable': True,
    'application': True,  # APPLICATION avec icône
    'sequence': 6,
}
