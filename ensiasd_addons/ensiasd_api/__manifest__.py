# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD API',
    'version': '17.0.1.1.0',
    'category': 'Education',
    'summary': 'API REST pour accès externe (Application mobile / Django)',
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
        - Stages (si ensiasd_stage installé)
        - Réclamations (si ensiasd_reclamation installé)

        Utilisé par l'application mobile/Django pour les étudiants.

        Routes HTTP disponibles :
          GET  /api/v1/health
          GET  /api/v1/info
          POST /api/v1/auth/login
          POST /api/v1/auth/logout
          POST /api/v1/auth/refresh
          GET  /api/v1/me
          PUT  /api/v1/me/password
          GET  /api/v1/notes
          GET  /api/v1/notes/summary
          GET  /api/v1/absences
          GET  /api/v1/absences/summary
          GET  /api/v1/emploi-temps
          GET  /api/v1/inscriptions
          GET  /api/v1/stages
          GET  /api/v1/annees
          GET  /api/v1/modules
          GET  /api/v1/reclamations
          POST /api/v1/reclamations
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
        # Modules optionnels — les routes correspondantes fonctionnent
        # même si ces modules ne sont pas installés (détection dynamique).
        # Décommentez si vous les installez :
        # 'ensiasd_stage',
        # 'ensiasd_timetable',
        # 'ensiasd_reclamation',
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
