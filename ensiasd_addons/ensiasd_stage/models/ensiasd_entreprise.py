# -*- coding: utf-8 -*-
from odoo import models, fields


class EnsiasdEntreprise(models.Model):
    """
    Entreprise partenaire.
    Hérite de res.partner pour profiter de l'intégration avec le module Contacts.
    """
    _name = 'ensiasd.entreprise'
    _description = 'Entreprise partenaire'
    _inherit = ['mail.thread']
    _order = 'name'

    # Lien vers res.partner (Contacts)
    partner_id = fields.Many2one('res.partner', string='Contact', ondelete='cascade',
                                  domain=[('is_company', '=', True)])
    
    name = fields.Char(string='Nom', required=True)
    address = fields.Text(string='Adresse')
    city = fields.Char(string='Ville')
    phone = fields.Char(string='Téléphone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Site Web')
    
    secteur = fields.Selection([
        ('tech', 'Technologies'),
        ('finance', 'Finance'),
        ('industrie', 'Industrie'),
        ('conseil', 'Conseil'),
        ('public', 'Secteur Public'),
        ('autre', 'Autre'),
    ], string='Secteur')
    
    contact_nom = fields.Char(string='Contact RH')
    contact_email = fields.Char(string='Email contact')
    contact_phone = fields.Char(string='Téléphone contact')
    
    stage_ids = fields.One2many('ensiasd.stage', 'entreprise_id', string='Stages')
    stage_count = fields.Integer(compute='_compute_stage_count')
    active = fields.Boolean(default=True)
    notes = fields.Text()

    def _compute_stage_count(self):
        for r in self:
            r.stage_count = len(r.stage_ids)
