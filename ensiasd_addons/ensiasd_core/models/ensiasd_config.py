# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdConfig(models.Model):
    _name = 'ensiasd.config'
    _description = 'Configuration ENSIASD'
    _rec_name = 'name'

    name = fields.Char(string='Nom de l\'établissement', required=True, default='ENSIASD')
    full_name = fields.Char(
        string='Nom complet',
        default='École Nationale Supérieure de l\'Intelligence Artificielle et Sciences des Données'
    )
    address = fields.Text(string='Adresse')
    city = fields.Char(string='Ville', default='Taroudant')
    phone = fields.Char(string='Téléphone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Site Web')
    logo = fields.Binary(string='Logo')
    
    # Paramètres de notation
    note_max = fields.Float(string='Note maximale', default=20.0)
    note_validation = fields.Float(string='Note de validation', default=12.0)
    note_elimination = fields.Float(string='Note éliminatoire', default=6.0)
    
    annee_courante_id = fields.Many2one('ensiasd.annee', string='Année courante',
                                         domain=[('is_current', '=', True)])

    @api.model
    def get_config(self):
        config = self.search([], limit=1)
        if not config:
            config = self.create({'name': 'ENSIASD'})
        return config
