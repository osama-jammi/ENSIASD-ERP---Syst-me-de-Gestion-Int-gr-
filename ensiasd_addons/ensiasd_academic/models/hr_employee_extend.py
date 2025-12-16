# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployeeAcademic(models.Model):
    """
    Extension de hr.employee pour ajouter les relations académiques.
    """
    _inherit = 'hr.employee'

    # Champ pour identifier les enseignants
    is_enseignant = fields.Boolean(string="Est enseignant")
    matricule_enseignant = fields.Char(string="Matricule enseignant")
    grade = fields.Char(string="Grade")
    specialite = fields.Char(string="Spécialité")
    date_recrutement = fields.Date(string="Date de recrutement")
    bureau = fields.Char(string="Bureau")

    # Relations académiques
    filiere_ids = fields.Many2many(
        'ensiasd.filiere',
        'hr_employee_filiere_rel',
        'employee_id',
        'filiere_id',
        string='Filières'
    )

    module_ids = fields.One2many(
        'ensiasd.module',
        'responsable_id',
        string='Modules responsable'
    )

    element_ids = fields.One2many(
        'ensiasd.element',
        'enseignant_id',
        string='Éléments enseignés'
    )