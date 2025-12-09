# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Étudiants',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Gestion complète des étudiants ENSIASD',
    'description': """
        Application de gestion des étudiants pour ENSIASD.
        
        Fonctionnalités:
        - Fiche étudiant complète (CNE, CIN, photo)
        - Inscription et réinscription avec workflow
        - Affectation aux filières et groupes
        - Historique du parcours académique
        - Intégration avec le module Contacts d'Odoo
    """,
    'author': 'ENSIASD - Jammi Osama',
    'website': 'https://ensiasd.ac.ma',
    'license': 'LGPL-3',
    
    'depends': [
        'ensiasd_core',
        'contacts',  # Intégration avec le module Contacts Odoo
        'mail',
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/ensiasd_student_views.xml',
        'views/ensiasd_groupe_views.xml',
        'views/ensiasd_menu.xml',
    ],
    
    'installable': True,
    'application': True,  # <<<< C'EST UNE APPLICATION avec icône
    'auto_install': False,
    'sequence': 2,
    
    # Icône de l'application (sera visible dans le menu principal)
    # Créer un fichier icon.png dans static/description/
}
