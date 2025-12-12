# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdInscriptionExtend(models.Model):
    """
    Extension du modèle Inscription pour le module grades
    Ajoute les champs liés aux notes
    """
    _inherit = 'ensiasd.inscription'

    # Notes liées
    note_ids = fields.One2many(
        'ensiasd.note',
        'inscription_id',
        string='Notes'
    )
    
    note_element_ids = fields.One2many(
        'ensiasd.note.element',
        'inscription_id',
        string='Notes par élément'
    )
    
    # Statistiques
    note_count = fields.Integer(
        string='Nombre de notes',
        compute='_compute_note_count'
    )
    
    moyenne_module = fields.Float(
        string='Moyenne du module',
        compute='_compute_moyenne',
        digits=(4, 2)
    )
    
    resultat_module = fields.Selection([
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('non_valide', 'Non validé'),
        ('rattrapage', 'Rattrapage'),
        ('elimine', 'Éliminé'),
    ], string='Résultat', compute='_compute_resultat')

    @api.depends('note_ids')
    def _compute_note_count(self):
        for record in self:
            record.note_count = len(record.note_ids)

    @api.depends('note_ids', 'note_ids.note_finale')
    def _compute_moyenne(self):
        """Calculer la moyenne des notes de cette inscription"""
        for record in self:
            notes = record.note_ids.filtered(lambda n: n.state in ['validated', 'locked'])
            if notes:
                # Prendre la note de la dernière session
                latest_note = notes.sorted('session_id', reverse=True)[0]
                record.moyenne_module = latest_note.note_finale
            else:
                record.moyenne_module = 0.0

    @api.depends('note_ids', 'note_ids.resultat')
    def _compute_resultat(self):
        """Déterminer le résultat final de l'inscription"""
        for record in self:
            notes = record.note_ids.filtered(lambda n: n.state in ['validated', 'locked'])
            if not notes:
                record.resultat_module = 'en_cours'
                continue
            
            # Prendre le résultat de la dernière session
            latest_note = notes.sorted('session_id', reverse=True)[0]
            record.resultat_module = latest_note.resultat

    def action_view_notes(self):
        """Afficher les notes de cette inscription"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Notes - {self.student_id.name} - {self.module_id.code}',
            'res_model': 'ensiasd.note',
            'view_mode': 'tree,form',
            'domain': [('inscription_id', '=', self.id)],
            'context': {
                'default_inscription_id': self.id,
            },
        }

    def action_view_note_elements(self):
        """Afficher les notes par élément"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Notes par élément - {self.student_id.name}',
            'res_model': 'ensiasd.note.element',
            'view_mode': 'tree,form',
            'domain': [('inscription_id', '=', self.id)],
            'context': {
                'default_inscription_id': self.id,
            },
        }
