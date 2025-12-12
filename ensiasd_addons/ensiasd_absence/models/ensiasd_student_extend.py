# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdStudentAbsenceExtend(models.Model):
    """
    Extension du modèle étudiant pour les statistiques d'absences
    """
    _inherit = 'ensiasd.student'

    absence_ids = fields.One2many(
        'ensiasd.absence',
        'student_id',
        string='Absences'
    )
    
    absence_count = fields.Integer(
        string='Nb absences',
        compute='_compute_absence_stats'
    )
    
    absence_count_justified = fields.Integer(
        string='Absences justifiées',
        compute='_compute_absence_stats'
    )
    
    absence_count_unjustified = fields.Integer(
        string='Absences non justifiées',
        compute='_compute_absence_stats'
    )
    
    total_heures_absence = fields.Float(
        string='Total heures absence',
        compute='_compute_absence_stats'
    )
    
    taux_assiduite = fields.Float(
        string='Taux d\'assiduité (%)',
        compute='_compute_taux_assiduite'
    )

    @api.depends('absence_ids', 'absence_ids.state')
    def _compute_absence_stats(self):
        for student in self:
            absences = student.absence_ids
            student.absence_count = len(absences)
            student.absence_count_justified = len(absences.filtered(lambda a: a.state in ['justified', 'excused']))
            student.absence_count_unjustified = len(absences.filtered(lambda a: a.state in ['absent', 'rejected']))
            student.total_heures_absence = sum(absences.mapped('heures_absence'))

    @api.depends('absence_ids')
    def _compute_taux_assiduite(self):
        for student in self:
            # Calculer le total des séances du groupe
            if student.groupe_id:
                total_seances = self.env['ensiasd.seance'].search_count([
                    ('groupe_ids', 'in', student.groupe_id.id),
                    ('state', '=', 'done'),
                ])
                if total_seances > 0:
                    presences = total_seances - student.absence_count
                    student.taux_assiduite = (presences / total_seances) * 100
                else:
                    student.taux_assiduite = 100.0
            else:
                student.taux_assiduite = 100.0

    def action_view_absences(self):
        """Voir les absences de l'étudiant"""
        self.ensure_one()
        return {
            'name': f'Absences - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'ensiasd.absence',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }
