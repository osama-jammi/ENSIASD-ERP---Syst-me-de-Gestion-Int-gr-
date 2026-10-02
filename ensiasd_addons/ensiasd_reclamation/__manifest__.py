# -*- coding: utf-8 -*-
{
    'name': 'ENSIASD Réclamations',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Gestion des réclamations étudiants (notes, absences, scolarité)',
    'description': """
        Module de gestion des réclamations pour ENSIASD :
        - Soumission de réclamations par les étudiants
        - Traitement et workflow par la scolarité et les enseignants
        - Suivi des réponses et historique
        - Intégration avec le portail étudiant via API REST
    """,
    'author': 'ENSIASD',
    'license': 'LGPL-3',
    'depends': [
        'ensiasd_core',
        'ensiasd_student',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/ensiasd_reclamation_views.xml',
        'views/ensiasd_menu.xml',
    ],
    'installable': True,
    'application': True,
    'sequence': 10,
}
