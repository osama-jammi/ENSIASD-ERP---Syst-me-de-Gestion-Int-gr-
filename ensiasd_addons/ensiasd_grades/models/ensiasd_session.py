# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdSession(models.Model):
    """
    Session d'examens (Normale ou Rattrapage)
    Permet de gérer les différentes sessions d'évaluation par année académique
    """
    _name = 'ensiasd.session'
    _description = 'Session d\'examens'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'annee_id desc, type_session, semestre'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    code = fields.Char(string='Code', required=True)
    
    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True,
        tracking=True
    )
    
    type_session = fields.Selection([
        ('normale', 'Session Normale'),
        ('rattrapage', 'Session Rattrapage'),
    ], string='Type de session', required=True, default='normale', tracking=True)
    
    semestre = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
        ('annuel', 'Annuel'),
    ], string='Semestre', required=True, tracking=True)
    
    date_debut = fields.Date(string='Date début', required=True, tracking=True)
    date_fin = fields.Date(string='Date fin', required=True, tracking=True)
    
    date_limite_saisie = fields.Date(
        string='Date limite de saisie',
        help="Date limite pour la saisie des notes par les enseignants"
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('open', 'Ouverte'),
        ('saisie', 'Saisie en cours'),
        ('closed', 'Clôturée'),
        ('deliberation', 'En délibération'),
        ('done', 'Terminée'),
    ], string='État', default='draft', tracking=True)
    
    note_ids = fields.One2many('ensiasd.note', 'session_id', string='Notes')
    note_count = fields.Integer(compute='_compute_note_count', string='Nombre de notes')
    
    filiere_ids = fields.Many2many(
        'ensiasd.filiere',
        'session_filiere_rel',
        'session_id',
        'filiere_id',
        string='Filières concernées'
    )
    
    is_current = fields.Boolean(string='Session en cours', default=False)
    allow_rattrapage = fields.Boolean(
        string='Permet le rattrapage',
        default=True,
        help="Si activé, les étudiants qui échouent peuvent passer le rattrapage"
    )
    
    observations = fields.Text(string='Observations')
    
    _sql_constraints = [
        ('code_annee_unique', 'UNIQUE(code, annee_id)',
         'Ce code de session existe déjà pour cette année!'),
    ]

    @api.depends('annee_id', 'type_session', 'semestre')
    def _compute_name(self):
        for record in self:
            if record.annee_id and record.type_session and record.semestre:
                session_type = dict(self._fields['type_session'].selection).get(record.type_session)
                sem = record.semestre if record.semestre != 'annuel' else 'Annuel'
                record.name = f"{record.annee_id.name} - {session_type} - {sem}"
            else:
                record.name = "Nouvelle session"

    @api.depends('note_ids')
    def _compute_note_count(self):
        for record in self:
            record.note_count = len(record.note_ids)

    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for record in self:
            if record.date_debut and record.date_fin:
                if record.date_fin < record.date_debut:
                    raise ValidationError("La date de fin doit être postérieure à la date de début!")

    def action_open(self):
        """Ouvrir la session pour la saisie des notes"""
        self.write({'state': 'open'})
        
    def action_start_saisie(self):
        """Démarrer la période de saisie"""
        self.write({'state': 'saisie'})

    def action_close(self):
        """Clôturer la session - plus de saisie possible"""
        self.write({'state': 'closed'})

    def action_deliberation(self):
        """Passer en mode délibération"""
        self.write({'state': 'deliberation'})

    def action_done(self):
        """Marquer la session comme terminée"""
        self.write({'state': 'done'})

    def action_reset_draft(self):
        """Remettre en brouillon"""
        self.write({'state': 'draft'})

    def action_view_notes(self):
        """Afficher les notes de cette session"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Notes - {self.name}',
            'res_model': 'ensiasd.note',
            'view_mode': 'tree,form',
            'domain': [('session_id', '=', self.id)],
            'context': {'default_session_id': self.id},
        }

    @api.model
    def get_current_session(self, semestre=None):
        """Récupérer la session en cours"""
        domain = [('is_current', '=', True)]
        if semestre:
            domain.append(('semestre', '=', semestre))
        return self.search(domain, limit=1)
