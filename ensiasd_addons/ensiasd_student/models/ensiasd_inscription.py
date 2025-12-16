# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdInscription(models.Model):
    """
    Inscription d'un étudiant à un module
    (Déplacé depuis ensiasd_academic)
    """
    _name = 'ensiasd.inscription'
    _description = 'Inscription à un module'
    _inherit = ['mail.thread']
    _order = 'annee_id desc, student_id'

    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        required=True,
        tracking=True,
        ondelete='cascade'
    )

    module_id = fields.Many2one(
        'ensiasd.module',
        string='Module',
        required=True,
        tracking=True,
        ondelete='cascade'
    )

    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True,
        tracking=True
    )

    # Champs relationnels pour faciliter les recherches
    filiere_id = fields.Many2one(
        related='student_id.filiere_id',
        string='Filière',
        store=True,
        readonly=True
    )

    semestre = fields.Selection(
        related='module_id.semestre',
        string='Semestre',
        store=True,
        readonly=True
    )

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('validated', 'Validée'),
        ('cancelled', 'Annulée'),
    ], string='État', default='draft', tracking=True)

    date_inscription = fields.Date(
        string='Date d\'inscription',
        default=fields.Date.today,
        tracking=True
    )

    # Statistiques (seront calculées par le module grades si installé)
    note_count = fields.Integer(
        string='Nombre de notes',
        compute='_compute_stats',
        store=False
    )

    moyenne_module = fields.Float(
        string='Moyenne',
        compute='_compute_stats',
        store=False,
        digits=(4, 2)
    )

    _sql_constraints = [
        ('unique_inscription',
         'UNIQUE(student_id, module_id, annee_id)',
         'Inscription déjà existante pour cet étudiant, ce module et cette année!'),
    ]

    def _compute_stats(self):
        """
        Calcule les statistiques si le module grades est installé
        """
        has_grades = 'ensiasd.note' in self.env

        for record in self:
            if has_grades:
                notes = self.env['ensiasd.note'].search([
                    ('inscription_id', '=', record.id),
                    ('state', 'in', ['validated', 'locked'])
                ])
                record.note_count = len(notes)

                if notes:
                    latest_note = notes.sorted('session_id', reverse=True)[0]
                    record.moyenne_module = latest_note.note_finale
                else:
                    record.moyenne_module = 0.0
            else:
                record.note_count = 0
                record.moyenne_module = 0.0

    def name_get(self):
        return [(r.id, f"{r.student_id.name} - {r.module_id.code}") for r in self]

    def action_confirm(self):
        """Confirmer l'inscription"""
        self.write({'state': 'confirmed'})

    def action_validate(self):
        """Valider l'inscription"""
        self.write({'state': 'validated'})

    def action_cancel(self):
        """Annuler l'inscription"""
        self.write({'state': 'cancelled'})

    def action_view_notes(self):
        """
        Voir les notes (si module grades installé)
        """
        self.ensure_one()

        if 'ensiasd.note' not in self.env:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Module non installé',
                    'message': 'Le module de gestion des notes n\'est pas installé.',
                    'type': 'warning',
                }
            }

        return {
            'type': 'ir.actions.act_window',
            'name': f'Notes - {self.student_id.name} - {self.module_id.code}',
            'res_model': 'ensiasd.note',
            'view_mode': 'tree,form',
            'domain': [('inscription_id', '=', self.id)],
            'context': {'default_inscription_id': self.id},
        }