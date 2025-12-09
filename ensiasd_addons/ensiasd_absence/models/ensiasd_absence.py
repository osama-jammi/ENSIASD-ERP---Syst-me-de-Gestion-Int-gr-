# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdAbsence(models.Model):
    _name = 'ensiasd.absence'
    _description = 'Absence'
    _order = 'seance_id desc, student_id'

    student_id = fields.Many2one('ensiasd.student', string='Étudiant', required=True)
    seance_id = fields.Many2one('ensiasd.seance', string='Séance', required=True)
    date = fields.Date(related='seance_id.date', store=True)
    module_id = fields.Many2one(related='seance_id.element_id.module_id', store=True)
    
    justifiee = fields.Boolean(string='Justifiée', default=False)
    motif = fields.Text(string='Motif')
    justificatif = fields.Binary(string='Justificatif', attachment=True)
    justificatif_filename = fields.Char()
    
    state = fields.Selection([
        ('absent', 'Absent'),
        ('justified', 'Justifié'),
        ('excused', 'Excusé'),
    ], string='État', default='absent')

    _sql_constraints = [
        ('unique_absence', 'UNIQUE(student_id, seance_id)', 'Absence déjà enregistrée!'),
    ]

    @api.onchange('justifiee')
    def _onchange_justifiee(self):
        self.state = 'justified' if self.justifiee else 'absent'

    def action_justify(self):
        self.write({'justifiee': True, 'state': 'justified'})

    def action_excuse(self):
        self.write({'state': 'excused'})
