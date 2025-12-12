# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdStudentExtend(models.Model):
    """
    Extension du modèle Étudiant pour le module grades
    Ajoute les champs liés aux notes et résultats
    """
    _inherit = 'ensiasd.student'

    # Notes et résultats
    note_ids = fields.One2many(
        'ensiasd.note',
        'student_id',
        string='Notes'
    )
    
    resultat_ids = fields.One2many(
        'ensiasd.resultat',
        'student_id',
        string='Résultats'
    )
    
    bulletin_ids = fields.One2many(
        'ensiasd.bulletin',
        'student_id',
        string='Bulletins'
    )
    
    # Statistiques
    note_count = fields.Integer(
        compute='_compute_grades_stats',
        string='Nombre de notes'
    )
    
    resultat_count = fields.Integer(
        compute='_compute_grades_stats',
        string='Nombre de résultats'
    )
    
    bulletin_count = fields.Integer(
        compute='_compute_grades_stats',
        string='Nombre de bulletins'
    )
    
    moyenne_generale = fields.Float(
        compute='_compute_moyenne_generale',
        string='Moyenne générale',
        digits=(4, 2)
    )
    
    credits_cumules = fields.Integer(
        compute='_compute_credits',
        string='Crédits cumulés'
    )

    @api.depends('note_ids', 'resultat_ids', 'bulletin_ids')
    def _compute_grades_stats(self):
        for record in self:
            record.note_count = len(record.note_ids)
            record.resultat_count = len(record.resultat_ids)
            record.bulletin_count = len(record.bulletin_ids)

    @api.depends('resultat_ids', 'resultat_ids.moyenne_ponderee')
    def _compute_moyenne_generale(self):
        """Calculer la moyenne générale sur tous les semestres"""
        for record in self:
            resultats = record.resultat_ids.filtered(
                lambda r: r.state in ['validated', 'locked'] and r.type_resultat != 'annee'
            )
            if resultats:
                record.moyenne_generale = sum(resultats.mapped('moyenne_ponderee')) / len(resultats)
            else:
                record.moyenne_generale = 0.0

    @api.depends('resultat_ids', 'resultat_ids.credits_valides')
    def _compute_credits(self):
        """Calculer les crédits cumulés"""
        for record in self:
            resultats = record.resultat_ids.filtered(
                lambda r: r.state in ['validated', 'locked'] and r.type_resultat != 'annee'
            )
            record.credits_cumules = sum(resultats.mapped('credits_valides'))

    def action_view_notes(self):
        """Afficher toutes les notes de l'étudiant"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Notes - {self.name}',
            'res_model': 'ensiasd.note',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_resultats(self):
        """Afficher tous les résultats"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Résultats - {self.name}',
            'res_model': 'ensiasd.resultat',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_bulletins(self):
        """Afficher tous les bulletins"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Bulletins - {self.name}',
            'res_model': 'ensiasd.bulletin',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_generate_bulletin(self):
        """Ouvrir l'assistant de génération de bulletin"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Générer un bulletin',
            'res_model': 'ensiasd.bulletin.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_student_id': self.id},
        }
