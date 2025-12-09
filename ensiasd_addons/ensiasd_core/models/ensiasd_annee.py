# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdAnnee(models.Model):
    _name = 'ensiasd.annee'
    _description = 'Année Universitaire'
    _order = 'date_debut desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Année Universitaire',
        required=True,
        tracking=True,
        help="Ex: 2024-2025"
    )
    code = fields.Char(string='Code', required=True)
    date_debut = fields.Date(string='Date de début', required=True, tracking=True)
    date_fin = fields.Date(string='Date de fin', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    is_current = fields.Boolean(string='Année en cours', default=False, tracking=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('open', 'Ouverte'),
        ('closed', 'Clôturée'),
    ], string='État', default='draft', tracking=True)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Cette année universitaire existe déjà!'),
    ]

    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for record in self:
            if record.date_debut and record.date_fin and record.date_debut >= record.date_fin:
                raise ValidationError("La date de début doit être antérieure à la date de fin!")

    def action_open(self):
        self.write({'state': 'open'})

    def action_close(self):
        self.write({'state': 'closed', 'is_current': False})

    def action_set_current(self):
        self.search([('is_current', '=', True)]).write({'is_current': False})
        self.write({'is_current': True, 'state': 'open'})
