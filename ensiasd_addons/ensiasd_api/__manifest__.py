# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD API',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'API REST pour accès externe (Application Django)',
    'description': """
        Module API REST pour ENSIASD
        ============================

        Ce module expose les données académiques via une API REST sécurisée:
        - Authentification étudiants (CNE/mot de passe)
        - Génération automatique des mots de passe (CNE+CIN)
        - Consultation des notes
        - Consultation des absences
        - Emploi du temps
        - Informations personnelles

        Utilisé par l'application Django pour les étudiants.
    """,
    'author': 'ENSIASD - Jammi Osama',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'ensiasd_core',
        'ensiasd_academic',
        'ensiasd_student',
        'ensiasd_grades',
        'ensiasd_absence',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/api_security.xml',
        'data/api_config_data.xml',
        'views/api_config_views.xml',
        'views/api_log_views.xml',
        'views/student_api_views.xml',
        'wizard/set_password_wizard_views.xml',
        'wizard/bulk_api_activation_wizard_views.xml',
        'views/ensiasd_menu.xml',
    ],
    'installable': True,
    'application': False,
    'sequence': 20,
}