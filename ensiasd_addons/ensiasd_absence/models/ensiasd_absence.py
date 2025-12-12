# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import hashlib
import secrets


class EnsiasdAbsence(models.Model):
    """
    Gestion des absences des étudiants
    """
    _name = 'ensiasd.absence'
    _description = 'Absence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, student_id'

    name = fields.Char(string='Référence', compute='_compute_name', store=True)
    
    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        required=True,
        tracking=True
    )
    
    student_cne = fields.Char(related='student_id.cne', string='CNE', store=True)
    student_groupe = fields.Many2one(related='student_id.groupe_id', string='Groupe', store=True)
    
    seance_id = fields.Many2one(
        'ensiasd.seance',
        string='Séance',
        required=True,
        tracking=True
    )
    
    date = fields.Date(
        related='seance_id.date',
        store=True,
        string='Date'
    )
    
    module_id = fields.Many2one(
        related='seance_id.element_id.module_id',
        store=True,
        string='Module'
    )
    
    element_id = fields.Many2one(
        related='seance_id.element_id',
        store=True,
        string='Élément'
    )
    
    enseignant_id = fields.Many2one(
        related='seance_id.enseignant_id',
        store=True,
        string='Enseignant'
    )
    
    type_seance = fields.Selection(
        related='seance_id.type_seance',
        store=True,
        string='Type séance'
    )
    
    # Justification
    justifiee = fields.Boolean(
        string='Justifiée',
        default=False,
        tracking=True
    )
    
    motif = fields.Text(string='Motif')
    
    justificatif = fields.Binary(
        string='Justificatif',
        attachment=True
    )
    justificatif_filename = fields.Char()
    
    date_justification = fields.Datetime(
        string='Date justification'
    )
    
    # État
    state = fields.Selection([
        ('absent', 'Absent'),
        ('pending', 'En attente de justification'),
        ('justified', 'Justifié'),
        ('excused', 'Excusé'),
        ('rejected', 'Justification rejetée'),
    ], string='État', default='absent', tracking=True)
    
    # Pour le suivi des notifications
    notification_sent = fields.Boolean(
        string='Notification envoyée',
        default=False
    )
    
    date_notification = fields.Datetime(
        string='Date notification'
    )
    
    # Compteur pour les statistiques
    heures_absence = fields.Float(
        string='Heures d\'absence',
        compute='_compute_heures',
        store=True
    )
    
    notes = fields.Text(string='Notes internes')

    _sql_constraints = [
        ('unique_absence', 'UNIQUE(student_id, seance_id)', 'Absence déjà enregistrée pour cet étudiant et cette séance!'),
    ]

    @api.depends('student_id', 'seance_id', 'date')
    def _compute_name(self):
        for record in self:
            if record.student_id and record.date:
                record.name = f"ABS/{record.student_id.matricule or record.student_id.id}/{record.date}"
            else:
                record.name = "Nouvelle absence"

    @api.depends('seance_id', 'seance_id.heure_debut', 'seance_id.heure_fin')
    def _compute_heures(self):
        for record in self:
            if record.seance_id:
                record.heures_absence = record.seance_id.heure_fin - record.seance_id.heure_debut
            else:
                record.heures_absence = 0

    @api.onchange('justifiee')
    def _onchange_justifiee(self):
        if self.justifiee:
            self.state = 'pending'
            self.date_justification = fields.Datetime.now()

    def action_mark_pending(self):
        """Marquer comme en attente de justification"""
        self.write({
            'state': 'pending',
            'date_justification': fields.Datetime.now(),
        })

    def action_justify(self):
        """Valider la justification"""
        self.write({
            'justifiee': True,
            'state': 'justified',
            'date_justification': fields.Datetime.now(),
        })

    def action_excuse(self):
        """Excuser l'absence"""
        self.write({
            'state': 'excused',
            'date_justification': fields.Datetime.now(),
        })

    def action_reject(self):
        """Rejeter la justification"""
        self.write({
            'state': 'rejected',
            'justifiee': False,
        })

    def action_reset(self):
        """Remettre à l'état absent"""
        self.write({
            'state': 'absent',
            'justifiee': False,
            'motif': False,
            'justificatif': False,
        })

    def action_send_notification(self):
        """Envoyer une notification à l'étudiant"""
        self.ensure_one()
        
        template = self.env.ref('ensiasd_absence.mail_template_absence_notification', raise_if_not_found=False)
        if template and self.student_id.email:
            template.send_mail(self.id, force_send=True)
            self.write({
                'notification_sent': True,
                'date_notification': fields.Datetime.now(),
            })
            return True
        return False

    @api.model
    def create(self, vals):
        """Surcharge pour envoyer notification automatiquement"""
        record = super().create(vals)
        
        # Envoyer notification automatiquement si configuré
        config = self.env['ir.config_parameter'].sudo()
        auto_notify = config.get_param('ensiasd_absence.auto_notify_student', 'True')
        
        if auto_notify == 'True':
            record.action_send_notification()
        
        return record

    @api.model
    def get_student_absences_stats(self, student_id, annee_id=None):
        """Obtenir les statistiques d'absences d'un étudiant"""
        domain = [('student_id', '=', student_id)]
        
        if annee_id:
            # Filtrer par année académique
            annee = self.env['ensiasd.annee'].browse(annee_id)
            domain += [
                ('date', '>=', annee.date_debut),
                ('date', '<=', annee.date_fin),
            ]
        
        absences = self.search(domain)
        
        return {
            'total': len(absences),
            'justifiees': len(absences.filtered(lambda a: a.state in ['justified', 'excused'])),
            'non_justifiees': len(absences.filtered(lambda a: a.state in ['absent', 'rejected'])),
            'en_attente': len(absences.filtered(lambda a: a.state == 'pending')),
            'heures_total': sum(absences.mapped('heures_absence')),
            'heures_justifiees': sum(absences.filtered(lambda a: a.state in ['justified', 'excused']).mapped('heures_absence')),
        }


class EnsiasdAbsenceToken(models.Model):
    """
    Tokens pour les formulaires d'appel par email
    """
    _name = 'ensiasd.absence.token'
    _description = 'Token formulaire absence'

    token = fields.Char(string='Token', required=True, index=True)
    seance_id = fields.Many2one('ensiasd.seance', string='Séance', required=True, ondelete='cascade')
    enseignant_id = fields.Many2one('hr.employee', string='Enseignant')
    date_creation = fields.Datetime(string='Date création', default=fields.Datetime.now)
    date_expiration = fields.Datetime(string='Date expiration')
    used = fields.Boolean(string='Utilisé', default=False)
    date_utilisation = fields.Datetime(string='Date utilisation')

    @api.model
    def create_token(self, seance_id, enseignant_id=None, validity_hours=48):
        """Créer un token pour un formulaire d'appel"""
        token = secrets.token_urlsafe(32)
        expiration = datetime.now() + timedelta(hours=validity_hours)
        
        return self.create({
            'token': token,
            'seance_id': seance_id,
            'enseignant_id': enseignant_id,
            'date_expiration': expiration,
        })

    def is_valid(self):
        """Vérifier si le token est valide"""
        self.ensure_one()
        if self.used:
            return False
        if self.date_expiration and fields.Datetime.now() > self.date_expiration:
            return False
        return True

    def mark_used(self):
        """Marquer le token comme utilisé"""
        self.write({
            'used': True,
            'date_utilisation': fields.Datetime.now(),
        })
