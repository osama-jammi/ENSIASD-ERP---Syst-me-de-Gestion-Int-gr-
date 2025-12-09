# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Académique',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Gestion académique - Filières, Modules, Semestres',
    'description': """
        Application de gestion académique pour ENSIASD.
        
        Fonctionnalités:
        - Gestion des filières (IA, Data Science, Big Data...)
        - Configuration des semestres (S1-S6)
        - Modules avec crédits ECTS
        - Éléments de module (CM, TD, TP)
        - Planning des séances
    """,
    'author': 'ENSIASD - Jammi Osama',
    'license': 'LGPL-3',
    
    'depends': [
        'ensiasd_core',
        'ensiasd_student',
        'hr',  # Pour les enseignants
    ],
    
    'data': [
        'security/ir.model.access.csv',
        'data/ensiasd_academic_data.xml',
        'views/ensiasd_filiere_views.xml',
        'views/ensiasd_module_views.xml',
        'views/ensiasd_element_views.xml',
        'views/ensiasd_seance_views.xml',
        'views/ensiasd_inscription_views.xml',
        'views/hr_employee_views.xml',
        'views/ensiasd_menu.xml',
    ],
    
    'installable': True,
    'application': True,  # APPLICATION avec icône
    'sequence': 3,
}
