# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Rapports',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Rapports et documents officiels',
    'author': 'ENSIASD - Jammi Osama',
    'license': 'LGPL-3',
    'depends': ['ensiasd_core', 'ensiasd_student', 'ensiasd_academic', 'ensiasd_grades'],
    'data': [
        'reports/report_releve_notes.xml',
        'reports/report_attestation.xml',
    ],
    'installable': True,
    'application': False,
    'sequence': 7,
}
