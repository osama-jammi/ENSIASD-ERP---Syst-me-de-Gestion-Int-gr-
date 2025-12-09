# -*- coding: utf-8 -*-
from odoo import models, fields


class EnsiasdSalleExtend(models.Model):
    """
    Extension de ensiasd.salle pour ajouter la relation vers les séances.
    Ceci résout le problème de dépendance circulaire.
    """
    _inherit = 'ensiasd.salle'

    seance_ids = fields.One2many('ensiasd.seance', 'salle_id', string='Séances')
    seance_count = fields.Integer(compute='_compute_seance_count')

    def _compute_seance_count(self):
        for r in self:
            r.seance_count = len(r.seance_ids)
