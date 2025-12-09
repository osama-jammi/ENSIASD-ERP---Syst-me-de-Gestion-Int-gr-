# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Absences',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Gestion des absences',
    'author': 'ENSIASD - Jammi Osama',
    'license': 'LGPL-3',
    'depends': ['ensiasd_core', 'ensiasd_student', 'ensiasd_academic'],
    'data': [
        'security/ir.model.access.csv',
        'views/ensiasd_absence_views.xml',
        'views/ensiasd_menu.xml',
    ],
    'installable': True,
    'application': False,
    'sequence': 5,
}
