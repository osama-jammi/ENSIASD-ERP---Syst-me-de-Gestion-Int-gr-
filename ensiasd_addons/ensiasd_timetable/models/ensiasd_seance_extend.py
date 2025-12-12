# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdSeanceExtend(models.Model):
    """
    Extension du modèle séance pour le lier à l'emploi du temps
    """
    _inherit = 'ensiasd.seance'

    emploi_id = fields.Many2one(
        'ensiasd.emploi',
        string='Emploi du temps',
        ondelete='set null',
        help="Emploi du temps ayant généré cette séance"
    )
    
    emploi_ligne_id = fields.Many2one(
        'ensiasd.emploi.ligne',
        string='Ligne EDT',
        ondelete='set null'
    )
    
    is_generated = fields.Boolean(
        string='Générée automatiquement',
        default=False,
        help="Indique si la séance a été générée automatiquement"
    )
    
    # Champs pour la gestion des absences
    absence_ids = fields.One2many(
        'ensiasd.absence',
        'seance_id',
        string='Absences'
    )
    
    absence_count = fields.Integer(
        string='Nb absents',
        compute='_compute_absence_count'
    )
    
    presence_count = fields.Integer(
        string='Nb présents',
        compute='_compute_presence_count'
    )
    
    total_etudiants = fields.Integer(
        string='Total étudiants',
        compute='_compute_total_etudiants'
    )
    
    taux_presence = fields.Float(
        string='Taux présence (%)',
        compute='_compute_taux_presence'
    )
    
    appel_fait = fields.Boolean(
        string='Appel effectué',
        default=False
    )
    
    date_appel = fields.Datetime(
        string='Date appel'
    )

    @api.depends('absence_ids')
    def _compute_absence_count(self):
        for record in self:
            record.absence_count = len(record.absence_ids)

    @api.depends('groupe_ids', 'groupe_ids.student_ids')
    def _compute_total_etudiants(self):
        for record in self:
            students = self.env['ensiasd.student']
            for groupe in record.groupe_ids:
                students |= groupe.student_ids
            record.total_etudiants = len(students)

    @api.depends('total_etudiants', 'absence_count')
    def _compute_presence_count(self):
        for record in self:
            record.presence_count = record.total_etudiants - record.absence_count

    @api.depends('total_etudiants', 'presence_count')
    def _compute_taux_presence(self):
        for record in self:
            if record.total_etudiants > 0:
                record.taux_presence = (record.presence_count / record.total_etudiants) * 100
            else:
                record.taux_presence = 0.0

    def action_view_absences(self):
        """Voir les absences de la séance"""
        self.ensure_one()
        return {
            'name': f'Absences - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'ensiasd.absence',
            'view_mode': 'tree,form',
            'domain': [('seance_id', '=', self.id)],
            'context': {'default_seance_id': self.id},
        }

    def action_open_appel(self):
        """Ouvrir le formulaire d'appel"""
        self.ensure_one()
        return {
            'name': f'Appel - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'ensiasd.appel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_seance_id': self.id,
            },
        }

    def action_send_appel_email(self):
        """Envoyer le formulaire d'appel par email à l'enseignant"""
        self.ensure_one()
        
        if not self.enseignant_id:
            return
        
        # Trouver le template
        template = self.env.ref('ensiasd_absence.mail_template_appel_seance', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        return True
