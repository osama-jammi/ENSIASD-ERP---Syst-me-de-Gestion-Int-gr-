# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    """
    Extension du modèle hr.employee d'Odoo pour ajouter les champs spécifiques
    aux enseignants ENSIASD.
    
    Ceci permet d'utiliser le module Employés (hr) d'Odoo tout en ajoutant
    les fonctionnalités spécifiques à l'école.
    """
    _inherit = 'hr.employee'

    # Champs spécifiques ENSIASD
    is_enseignant = fields.Boolean(string='Est enseignant', default=False)
    matricule_enseignant = fields.Char(string='Matricule enseignant')
    grade = fields.Selection([
        ('pa', 'Professeur Assistant'),
        ('ph', 'Professeur Habilité'),
        ('pes', 'Professeur de l\'Enseignement Supérieur'),
        ('vacataire', 'Vacataire'),
    ], string='Grade')
    specialite = fields.Char(string='Spécialité')
    
    # Relation avec les filières (sera définie dans ensiasd_academic)
    # filiere_ids = fields.Many2many('ensiasd.filiere', string='Filières')
    
    date_recrutement = fields.Date(string='Date de recrutement')
    bureau = fields.Char(string='Bureau')
