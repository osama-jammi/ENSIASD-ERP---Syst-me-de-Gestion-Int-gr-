# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdInscription(models.Model):
    _name = 'ensiasd.inscription'
    _description = 'Inscription à un module'
    _inherit = ['mail.thread']
    _order = 'annee_id desc, student_id'

    student_id = fields.Many2one('ensiasd.student', string='Étudiant', required=True, tracking=True)
    module_id = fields.Many2one('ensiasd.module', string='Module', required=True, tracking=True)
    annee_id = fields.Many2one('ensiasd.annee', string='Année', required=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('validated', 'Validée'),
        ('cancelled', 'Annulée'),
    ], string='État', default='draft', tracking=True)
    
    date_inscription = fields.Date(string='Date', default=fields.Date.today)

    _sql_constraints = [
        ('unique_inscription', 'UNIQUE(student_id, module_id, annee_id)', 
         'Inscription déjà existante!'),
    ]

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_validate(self):
        self.write({'state': 'validated'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def name_get(self):
        return [(r.id, f"{r.student_id.name} - {r.module_id.code}") for r in self]
