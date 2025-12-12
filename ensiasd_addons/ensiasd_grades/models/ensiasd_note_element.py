# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdNoteElement(models.Model):
    """
    Note par élément de module
    Permet une granularité plus fine que les notes par module
    """
    _name = 'ensiasd.note.element'
    _description = 'Note par élément'
    _inherit = ['mail.thread']
    _order = 'inscription_id, element_id, type_eval'

    name = fields.Char(compute='_compute_name', store=True)
    
    inscription_id = fields.Many2one(
        'ensiasd.inscription',
        string='Inscription',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    student_id = fields.Many2one(
        related='inscription_id.student_id',
        store=True,
        string='Étudiant'
    )
    
    module_id = fields.Many2one(
        related='inscription_id.module_id',
        store=True,
        string='Module'
    )
    
    element_id = fields.Many2one(
        'ensiasd.element',
        string='Élément',
        required=True,
        domain="[('module_id', '=', module_id)]",
        tracking=True
    )
    
    annee_id = fields.Many2one(
        related='inscription_id.annee_id',
        store=True,
        string='Année'
    )
    
    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session',
        tracking=True
    )
    
    type_eval = fields.Selection([
        ('cc1', 'CC 1'),
        ('cc2', 'CC 2'),
        ('cc3', 'CC 3'),
        ('tp', 'TP'),
        ('projet', 'Projet'),
        ('examen', 'Examen'),
        ('rattrapage', 'Rattrapage'),
        ('oral', 'Oral'),
    ], string='Type d\'évaluation', required=True, tracking=True)
    
    valeur = fields.Float(
        string='Note',
        digits=(4, 2),
        tracking=True
    )
    
    coefficient = fields.Float(
        string='Coefficient',
        default=1.0
    )
    
    date_eval = fields.Date(
        string='Date d\'évaluation',
        default=fields.Date.today
    )
    
    enseignant_id = fields.Many2one(
        'hr.employee',
        string='Évaluateur',
        domain=[('is_enseignant', '=', True)]
    )
    
    is_absent = fields.Boolean(
        string='Absent',
        default=False,
        help="L'étudiant était absent à cette évaluation"
    )
    
    is_justified = fields.Boolean(
        string='Absence justifiée',
        default=False
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('validated', 'Validée'),
        ('locked', 'Verrouillée'),
    ], string='État', default='draft', tracking=True)
    
    observations = fields.Text(string='Observations')

    _sql_constraints = [
        ('unique_note_element',
         'UNIQUE(inscription_id, element_id, type_eval, session_id)',
         'Une note existe déjà pour cet étudiant, cet élément, ce type et cette session!'),
    ]

    @api.depends('student_id', 'element_id', 'type_eval')
    def _compute_name(self):
        for record in self:
            if record.student_id and record.element_id and record.type_eval:
                type_label = dict(self._fields['type_eval'].selection).get(record.type_eval)
                record.name = f"{record.student_id.name} - {record.element_id.name} - {type_label}"
            else:
                record.name = "Nouvelle note"

    @api.constrains('valeur')
    def _check_valeur(self):
        config = self.env['ensiasd.config'].get_config()
        for record in self:
            if not record.is_absent:
                if record.valeur < 0 or record.valeur > config.note_max:
                    raise ValidationError(
                        f"La note doit être comprise entre 0 et {config.note_max}!"
                    )

    @api.onchange('is_absent')
    def _onchange_is_absent(self):
        if self.is_absent:
            self.valeur = 0.0

    def action_confirm(self):
        """Confirmer la note"""
        self.write({'state': 'confirmed'})

    def action_validate(self):
        """Valider la note"""
        self.write({'state': 'validated'})

    def action_lock(self):
        """Verrouiller la note (après délibération)"""
        self.write({'state': 'locked'})

    def action_reset_draft(self):
        """Remettre en brouillon"""
        for record in self:
            if record.state == 'locked':
                raise ValidationError(
                    "Impossible de modifier une note verrouillée après délibération!"
                )
        self.write({'state': 'draft'})
