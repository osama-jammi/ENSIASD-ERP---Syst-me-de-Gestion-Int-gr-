# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdStage(models.Model):
    _name = 'ensiasd.stage'
    _description = 'Stage / PFE'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_debut desc'

    name = fields.Char(string='Référence', readonly=True, copy=False, default='Nouveau')
    sujet = fields.Char(string='Sujet', required=True, tracking=True)
    description = fields.Text()
    
    student_id = fields.Many2one('ensiasd.student', string='Étudiant', required=True, tracking=True)
    entreprise_id = fields.Many2one('ensiasd.entreprise', string='Entreprise', required=True, tracking=True)
    
    type_stage = fields.Selection([
        ('observation', 'Stage d\'observation'),
        ('technicien', 'Stage technicien'),
        ('pfe', 'Projet de Fin d\'Études'),
    ], string='Type', required=True, tracking=True)
    
    date_debut = fields.Date(string='Début', required=True)
    date_fin = fields.Date(string='Fin', required=True)
    duree = fields.Integer(string='Durée (sem)', compute='_compute_duree')
    
    encadrant_interne_id = fields.Many2one('hr.employee', string='Encadrant interne',
                                           domain=[('is_enseignant', '=', True)])
    encadrant_externe = fields.Char(string='Encadrant externe')
    
    annee_id = fields.Many2one('ensiasd.annee', string='Année')
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('in_progress', 'En cours'),
        ('defense', 'Soutenance'),
        ('done', 'Terminé'),
        ('cancelled', 'Annulé'),
    ], string='État', default='draft', tracking=True)
    
    date_soutenance = fields.Datetime(string='Date soutenance')
    note_finale = fields.Float(string='Note', digits=(4, 2))
    mention = fields.Selection([
        ('passable', 'Passable'),
        ('ab', 'Assez Bien'),
        ('bien', 'Bien'),
        ('tb', 'Très Bien'),
    ], string='Mention')
    
    rapport = fields.Binary(string='Rapport', attachment=True)
    rapport_filename = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('ensiasd.stage') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('date_debut', 'date_fin')
    def _compute_duree(self):
        for r in self:
            if r.date_debut and r.date_fin:
                r.duree = (r.date_fin - r.date_debut).days // 7
            else:
                r.duree = 0

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_defense(self):
        self.write({'state': 'defense'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
