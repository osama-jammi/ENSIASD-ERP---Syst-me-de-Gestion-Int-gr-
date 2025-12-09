# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    """
    Intégration dans les Paramètres Odoo (Settings).
    Permet de configurer ENSIASD depuis Configuration > Paramètres généraux
    """
    _inherit = 'res.config.settings'

    ensiasd_school_name = fields.Char(
        string='Nom de l\'école',
        config_parameter='ensiasd.school_name',
        default='ENSIASD'
    )
    ensiasd_note_max = fields.Float(
        string='Note maximale',
        config_parameter='ensiasd.note_max',
        default=20.0
    )
    ensiasd_note_validation = fields.Float(
        string='Note de validation',
        config_parameter='ensiasd.note_validation',
        default=12.0
    )
    ensiasd_annee_courante_id = fields.Many2one(
        'ensiasd.annee',
        string='Année universitaire courante',
        config_parameter='ensiasd.annee_courante_id'
    )
