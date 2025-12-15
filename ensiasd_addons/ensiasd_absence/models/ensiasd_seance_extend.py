# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdSeanceAbsence(models.Model):
    """
    Extension du modèle séance pour ajouter les champs liés aux absences.
    """
    _inherit = 'ensiasd.seance'

    # Relation avec les absences
    absence_ids = fields.One2many(
        'ensiasd.absence',
        'seance_id',
        string='Absences'
    )

    absence_count = fields.Integer(
        string='Nb absents',
        compute='_compute_absence_stats',
        store=True
    )

    presence_count = fields.Integer(
        string='Nb présents',
        compute='_compute_absence_stats',
        store=True
    )

    total_etudiants = fields.Integer(
        string='Total étudiants',
        compute='_compute_total_etudiants',
        store=True
    )

    taux_presence = fields.Float(
        string='Taux présence (%)',
        compute='_compute_absence_stats',
        store=True
    )

    appel_fait = fields.Boolean(
        string='Appel effectué',
        default=False
    )

    date_appel = fields.Datetime(
        string='Date appel'
    )

    # Token pour l'accès au formulaire web
    appel_token = fields.Char(
        string='Token d\'appel',
        copy=False,
        readonly=True
    )

    @api.depends('groupe_ids', 'groupe_ids.student_ids')
    def _compute_total_etudiants(self):
        for record in self:
            students = self.env['ensiasd.student']
            for groupe in record.groupe_ids:
                students |= groupe.student_ids.filtered(lambda s: s.state == 'actif')
            record.total_etudiants = len(students)

    @api.depends('absence_ids', 'total_etudiants')
    def _compute_absence_stats(self):
        for record in self:
            record.absence_count = len(record.absence_ids)
            record.presence_count = record.total_etudiants - record.absence_count
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
        """Ouvrir le wizard d'appel"""
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
        """Envoyer le formulaire d'appel par email"""
        self.ensure_one()

        if not self.enseignant_id:
            return

        # Générer un token si nécessaire
        if not self.appel_token:
            import uuid
            self.appel_token = str(uuid.uuid4())

        # Trouver le template
        template = self.env.ref('ensiasd_absence.mail_template_appel_seance', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

        return True