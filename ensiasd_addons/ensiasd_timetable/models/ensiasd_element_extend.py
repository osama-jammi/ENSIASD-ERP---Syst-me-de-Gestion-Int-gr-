# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdElementExtend(models.Model):
    """
    Extension de ensiasd.element pour ajouter la relation vers les séances.
    """
    _inherit = 'ensiasd.element'

    seance_ids = fields.One2many('ensiasd.seance', 'element_id', string='Séances')
    seance_count = fields.Integer(compute='_compute_seance_count', string='Nombre de séances')

    @api.depends('seance_ids')
    def _compute_seance_count(self):
        for r in self:
            r.seance_count = len(r.seance_ids)