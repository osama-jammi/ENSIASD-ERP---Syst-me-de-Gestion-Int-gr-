# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdGroupe(models.Model):
    _name = 'ensiasd.groupe'
    _description = 'Groupe d\'étudiants'
    _order = 'name'

    name = fields.Char(string='Nom du groupe', required=True)
    code = fields.Char(string='Code', required=True)
    niveau = fields.Selection([
        ('1', '1ère année'),
        ('2', '2ème année'),
        ('3', '3ème année'),
    ], string='Niveau', required=True)
    
    annee_id = fields.Many2one('ensiasd.annee', string='Année universitaire', required=True)
    student_ids = fields.One2many('ensiasd.student', 'groupe_id', string='Étudiants')
    student_count = fields.Integer(string='Nb étudiants', compute='_compute_student_count')
    capacite = fields.Integer(string='Capacité max', default=30)
    active = fields.Boolean(string='Actif', default=True)

    @api.depends('student_ids')
    def _compute_student_count(self):
        for record in self:
            record.student_count = len(record.student_ids)
