# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdFiliere(models.Model):
    _name = 'ensiasd.filiere'
    _description = 'Filière'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nom', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    description = fields.Text(string='Description')
    
    niveau = fields.Selection([
        ('licence', 'Licence'),
        ('master', 'Master'),
        ('ingenieur', 'Cycle Ingénieur'),
    ], string='Niveau', default='ingenieur')
    duree = fields.Integer(string='Durée (années)', default=3)
    
    # Lien vers hr.employee pour le responsable
    responsable_id = fields.Many2one('hr.employee', string='Responsable',
                                      domain=[('is_enseignant', '=', True)])
    
    module_ids = fields.One2many('ensiasd.module', 'filiere_id', string='Modules')
    module_count = fields.Integer(compute='_compute_module_count')
    active = fields.Boolean(default=True)
    color = fields.Integer()

    _sql_constraints = [('code_unique', 'UNIQUE(code)', 'Ce code existe déjà!')]

    @api.depends('module_ids')
    def _compute_module_count(self):
        for r in self:
            r.module_count = len(r.module_ids)
