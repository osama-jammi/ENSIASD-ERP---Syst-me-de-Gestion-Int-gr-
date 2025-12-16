# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Académique',
    'version': '17.0.2.1.0',
    'category': 'Education',
    'summary': 'Gestion académique - Filières, Modules, Éléments, Enseignants',
    'description': """
        Application de gestion académique pour ENSIASD.

        Fonctionnalités:
        - Gestion des filières (IA, Data Science, Big Data...)
        - Configuration des semestres (S1-S6)
        - Modules avec crédits ECTS
        - Éléments de module (CM, TD, TP)
        - Gestion des enseignants avec workflow
        - Extension des enseignants (hr.employee)

        Note: Les inscriptions sont gérées dans le module ensiasd_student
    """,
    'author': 'ENSIASD - Jammi Osama',
    'license': 'LGPL-3',

    'depends': [
        'ensiasd_core',
        'hr',
        'resource',
    ],

    'data': [
        'security/ensiasd_academic_security.xml',
        'security/ir.model.access.csv',
        'data/ensiasd_academic_data.xml',
        'views/ensiasd_filiere_views.xml',
        'views/ensiasd_module_views.xml',
        'views/ensiasd_element_views.xml',
        'views/hr_employee_views.xml',
        'views/ensiasd_menu.xml',
    ],

    'installable': True,
    'application': True,
    'sequence': 3,
    'auto_install': False,
}