# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdSeance(models.Model):
    _name = 'ensiasd.seance'
    _description = 'Séance de cours'
    _order = 'date desc, heure_debut'

    name = fields.Char(compute='_compute_name', store=True)
    element_id = fields.Many2one('ensiasd.element', string='Élément', required=True, ondelete='cascade')
    
    date = fields.Date(string='Date', required=True)
    heure_debut = fields.Float(string='Heure début', required=True)
    heure_fin = fields.Float(string='Heure fin', required=True)
    
    salle_id = fields.Many2one('ensiasd.salle', string='Salle', required=True)
    enseignant_id = fields.Many2one('hr.employee', string='Enseignant',
                                     domain=[('is_enseignant', '=', True)])
    groupe_ids = fields.Many2many('ensiasd.groupe', string='Groupes')
    
    type_seance = fields.Selection(related='element_id.type_element', store=True)
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('done', 'Effectuée'),
        ('cancelled', 'Annulée'),
    ], string='État', default='planned')
    notes = fields.Text(string='Notes')

    @api.depends('element_id', 'date')
    def _compute_name(self):
        for r in self:
            r.name = f"{r.element_id.module_id.code} - {r.date}" if r.element_id and r.date else "Nouvelle"

    @api.constrains('heure_debut', 'heure_fin')
    def _check_heures(self):
        for r in self:
            if r.heure_debut >= r.heure_fin:
                raise ValidationError("L'heure de fin doit être après l'heure de début!")

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
