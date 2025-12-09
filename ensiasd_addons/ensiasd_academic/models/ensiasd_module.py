# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdModule(models.Model):
    _name = 'ensiasd.module'
    _description = 'Module académique'
    _inherit = ['mail.thread']
    _order = 'semestre, code'

    name = fields.Char(string='Nom', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    description = fields.Text(string='Description')
    
    filiere_id = fields.Many2one('ensiasd.filiere', string='Filière', required=True)
    
    semestre = fields.Selection([
        ('S1', 'Semestre 1'), ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'), ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'), ('S6', 'Semestre 6'),
    ], string='Semestre', required=True)
    
    credits_ects = fields.Integer(string='Crédits ECTS', default=3)
    coefficient = fields.Float(string='Coefficient', default=1.0)
    volume_horaire = fields.Integer(compute='_compute_volume_horaire', store=True)
    
    type_module = fields.Selection([
        ('obligatoire', 'Obligatoire'),
        ('optionnel', 'Optionnel'),
    ], string='Type', default='obligatoire')
    
    responsable_id = fields.Many2one('hr.employee', string='Responsable',
                                      domain=[('is_enseignant', '=', True)])
    element_ids = fields.One2many('ensiasd.element', 'module_id', string='Éléments')
    prerequis_ids = fields.Many2many('ensiasd.module', 'ensiasd_module_prerequis_rel',
                                      'module_id', 'prerequis_id', string='Pré-requis')
    active = fields.Boolean(default=True)

    _sql_constraints = [('code_unique', 'UNIQUE(code)', 'Ce code existe déjà!')]

    @api.depends('element_ids.volume_horaire')
    def _compute_volume_horaire(self):
        for r in self:
            r.volume_horaire = sum(r.element_ids.mapped('volume_horaire'))
