# -*- coding: utf-8 -*-
from odoo import models, fields


class EnsiasdSalle(models.Model):
    _name = 'ensiasd.salle'
    _description = 'Salle de cours'
    _order = 'name'

    name = fields.Char(string='Nom de la salle', required=True)
    code = fields.Char(string='Code', required=True)
    batiment = fields.Char(string='Bâtiment')
    etage = fields.Char(string='Étage')
    capacite = fields.Integer(string='Capacité', default=30)
    type_salle = fields.Selection([
        ('cours', 'Salle de cours'),
        ('td', 'Salle TD'),
        ('tp', 'Salle TP/Laboratoire'),
        ('amphi', 'Amphithéâtre'),
        ('reunion', 'Salle de réunion'),
    ], string='Type de salle', default='cours')
    equipements = fields.Text(string='Équipements')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Ce code de salle existe déjà!'),
    ]

    def name_get(self):
        return [(r.id, f"[{r.code}] {r.name}") for r in self]