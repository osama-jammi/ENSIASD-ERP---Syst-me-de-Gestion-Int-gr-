# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class NoteSaisieWizard(models.TransientModel):
    """
    Assistant de saisie rapide des notes
    Permet de saisir les notes pour tous les étudiants d'un module
    """
    _name = 'ensiasd.note.saisie.wizard'
    _description = 'Assistant de saisie des notes'

    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session',
        required=True,
        default=lambda self: self._default_session(),
        domain=[('state', 'in', ['open', 'saisie'])]
    )
    
    module_id = fields.Many2one(
        'ensiasd.module',
        string='Module',
        required=True
    )
    
    element_id = fields.Many2one(
        'ensiasd.element',
        string='Élément',
        domain="[('module_id', '=', module_id)]"
    )
    
    type_eval = fields.Selection([
        ('cc1', 'CC 1'),
        ('cc2', 'CC 2'),
        ('cc3', 'CC 3'),
        ('tp', 'TP'),
        ('projet', 'Projet'),
        ('examen', 'Examen'),
        ('rattrapage', 'Rattrapage'),
    ], string='Type d\'évaluation', required=True, default='examen')
    
    date_eval = fields.Date(
        string='Date d\'évaluation',
        default=fields.Date.today
    )
    
    line_ids = fields.One2many(
        'ensiasd.note.saisie.wizard.line',
        'wizard_id',
        string='Notes à saisir'
    )
    
    state = fields.Selection([
        ('config', 'Configuration'),
        ('saisie', 'Saisie'),
        ('done', 'Terminé'),
    ], string='État', default='config')
    
    notes_count = fields.Integer(
        string='Notes saisies',
        compute='_compute_stats'
    )
    
    average = fields.Float(
        string='Moyenne',
        compute='_compute_stats',
        digits=(4, 2)
    )

    def _default_session(self):
        """Session par défaut = session en cours"""
        return self.env['ensiasd.session'].search([
            ('is_current', '=', True),
            ('state', 'in', ['open', 'saisie']),
        ], limit=1)

    @api.depends('line_ids', 'line_ids.note')
    def _compute_stats(self):
        for record in self:
            lines_with_notes = record.line_ids.filtered(lambda l: l.note > 0)
            record.notes_count = len(lines_with_notes)
            if lines_with_notes:
                record.average = sum(lines_with_notes.mapped('note')) / len(lines_with_notes)
            else:
                record.average = 0.0

    def action_load_students(self):
        """Charger les étudiants inscrits au module"""
        self.ensure_one()
        
        if not self.module_id or not self.session_id:
            raise UserError("Veuillez sélectionner un module et une session!")
        
        # Supprimer les lignes existantes
        self.line_ids.unlink()
        
        # Charger les inscriptions
        inscriptions = self.env['ensiasd.inscription'].search([
            ('module_id', '=', self.module_id.id),
            ('annee_id', '=', self.session_id.annee_id.id),
            ('state', '=', 'validated'),
        ])
        
        if not inscriptions:
            raise UserError("Aucun étudiant inscrit à ce module pour cette année!")
        
        # Créer les lignes
        lines = []
        for inscription in inscriptions:
            # Vérifier s'il existe déjà une note
            existing_note = self.env['ensiasd.note.element'].search([
                ('inscription_id', '=', inscription.id),
                ('type_eval', '=', self.type_eval),
                ('session_id', '=', self.session_id.id),
            ], limit=1)
            
            lines.append((0, 0, {
                'wizard_id': self.id,
                'inscription_id': inscription.id,
                'student_id': inscription.student_id.id,
                'student_cne': inscription.student_id.cne,
                'student_name': inscription.student_id.name,
                'note': existing_note.valeur if existing_note else 0.0,
                'is_absent': existing_note.is_absent if existing_note else False,
                'existing_note_id': existing_note.id if existing_note else False,
            }))
        
        self.write({
            'line_ids': lines,
            'state': 'saisie',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_save_notes(self):
        """Enregistrer toutes les notes"""
        self.ensure_one()
        
        saved = 0
        for line in self.line_ids:
            if line.note > 0 or line.is_absent:
                if line.existing_note_id:
                    # Mettre à jour la note existante
                    line.existing_note_id.write({
                        'valeur': line.note if not line.is_absent else 0.0,
                        'is_absent': line.is_absent,
                    })
                else:
                    # Créer une nouvelle note
                    self.env['ensiasd.note.element'].create({
                        'inscription_id': line.inscription_id.id,
                        'element_id': self.element_id.id if self.element_id else 
                                     (self.module_id.element_ids[0].id if self.module_id.element_ids else False),
                        'type_eval': self.type_eval,
                        'session_id': self.session_id.id,
                        'valeur': line.note if not line.is_absent else 0.0,
                        'is_absent': line.is_absent,
                        'date_eval': self.date_eval,
                    })
                saved += 1
        
        self.state = 'done'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notes enregistrées',
                'message': f'{saved} notes ont été enregistrées avec succès.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_back(self):
        """Retour à la configuration"""
        self.state = 'config'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class NoteSaisieWizardLine(models.TransientModel):
    """
    Ligne de l'assistant de saisie des notes
    """
    _name = 'ensiasd.note.saisie.wizard.line'
    _description = 'Ligne de saisie de note'
    _order = 'student_name'

    wizard_id = fields.Many2one(
        'ensiasd.note.saisie.wizard',
        string='Assistant',
        required=True,
        ondelete='cascade'
    )
    
    inscription_id = fields.Many2one(
        'ensiasd.inscription',
        string='Inscription',
        required=True
    )
    
    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        readonly=True
    )
    
    student_cne = fields.Char(
        string='CNE',
        readonly=True
    )
    
    student_name = fields.Char(
        string='Nom',
        readonly=True
    )
    
    note = fields.Float(
        string='Note',
        digits=(4, 2),
        default=0.0
    )
    
    is_absent = fields.Boolean(
        string='Absent',
        default=False
    )
    
    existing_note_id = fields.Many2one(
        'ensiasd.note.element',
        string='Note existante'
    )

    @api.constrains('note')
    def _check_note(self):
        config = self.env['ensiasd.config'].get_config()
        for record in self:
            if not record.is_absent and (record.note < 0 or record.note > config.note_max):
                raise ValidationError(
                    f"La note doit être comprise entre 0 et {config.note_max}!"
                )

    @api.onchange('is_absent')
    def _onchange_is_absent(self):
        if self.is_absent:
            self.note = 0.0
