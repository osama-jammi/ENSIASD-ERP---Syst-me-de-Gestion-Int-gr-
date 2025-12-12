# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Core',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Module de base pour ENSIASD ERP',
    'description': """
        Module de base contenant:
        - Configuration globale de l'école
        - Années universitaires
        - Salles et ressources
        - Groupes de sécurité communs
    """,
    'author': 'ENSIASD - Jammi Osama',
    'website': 'https://ensiasd.ac.ma',
    'license': 'LGPL-3',
    
    # Dépendances vers modules Odoo standards
    'depends': [
        'base',
        'mail',
        'hr',  # Pour les enseignants (employés)
    ],
    
    'data': [
        'security/ensiasd_security.xml',
        'security/ir.model.access.csv',
        'data/ensiasd_data.xml',
        'views/ensiasd_annee_views.xml',
        'views/ensiasd_config_views.xml',
        'views/ensiasd_salle_views.xml',
        'views/res_config_settings_views.xml',
        'views/ensiasd_menu.xml',
    ],
    
    'installable': True,
    'application': False,  # module de base
    'auto_install': False,
    'sequence': 1,
}
