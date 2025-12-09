# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdNote(models.Model):
    _name = 'ensiasd.note'
    _description = 'Note'
    _order = 'inscription_id, type_eval'

    inscription_id = fields.Many2one('ensiasd.inscription', string='Inscription', required=True, ondelete='cascade')
    student_id = fields.Many2one(related='inscription_id.student_id', store=True)
    module_id = fields.Many2one(related='inscription_id.module_id', store=True)
    annee_id = fields.Many2one(related='inscription_id.annee_id', store=True)
    
    type_eval = fields.Selection([
        ('cc', 'Contrôle Continu'),
        ('examen', 'Examen Final'),
        ('tp', 'TP/Pratique'),
        ('projet', 'Projet'),
        ('rattrapage', 'Rattrapage'),
    ], string='Type', required=True)
    
    valeur = fields.Float(string='Note', required=True, digits=(4, 2))
    coefficient = fields.Float(string='Coefficient', default=1.0)
    date_eval = fields.Date(string='Date', default=fields.Date.today)
    observations = fields.Text(string='Observations')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('validated', 'Validée'),
    ], string='État', default='draft')

    @api.constrains('valeur')
    def _check_valeur(self):
        for r in self:
            config = self.env['ensiasd.config'].get_config()
            if r.valeur < 0 or r.valeur > config.note_max:
                raise ValidationError(f"Note entre 0 et {config.note_max}!")

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_validate(self):
        self.write({'state': 'validated'})
