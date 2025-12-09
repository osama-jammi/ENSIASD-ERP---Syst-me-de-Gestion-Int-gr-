# -*- coding: utf-8 -*-
from odoo import models, fields


class EnsiasdElement(models.Model):
    _name = 'ensiasd.element'
    _description = 'Élément de module'
    _order = 'module_id, type_element'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code')
    module_id = fields.Many2one('ensiasd.module', string='Module', required=True, ondelete='cascade')
    
    type_element = fields.Selection([
        ('cm', 'Cours Magistral'),
        ('td', 'Travaux Dirigés'),
        ('tp', 'Travaux Pratiques'),
    ], string='Type', required=True)
    
    volume_horaire = fields.Integer(string='Volume horaire', default=20)
    coefficient = fields.Float(string='Coefficient', default=1.0)
    enseignant_id = fields.Many2one('hr.employee', string='Enseignant',
                                     domain=[('is_enseignant', '=', True)])
    seance_ids = fields.One2many('ensiasd.seance', 'element_id', string='Séances')

    def name_get(self):
        return [(r.id, f"{r.module_id.code} - {r.name} ({r.type_element.upper()})") for r in self]
