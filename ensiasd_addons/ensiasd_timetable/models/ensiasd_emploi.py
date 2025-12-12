# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class EnsiasdEmploi(models.Model):
    """
    Emploi du temps par filière/semestre/année
    """
    _name = 'ensiasd.emploi'
    _description = 'Emploi du temps'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'annee_id desc, filiere_id, semestre'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    
    filiere_id = fields.Many2one(
        'ensiasd.filiere',
        string='Filière',
        required=True,
        tracking=True
    )
    
    semestre = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
    ], string='Semestre', required=True, tracking=True)
    
    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True,
        tracking=True
    )
    
    groupe_ids = fields.Many2many(
        'ensiasd.groupe',
        string='Groupes concernés',
        help="Laisser vide pour tous les groupes de la filière"
    )
    
    date_debut = fields.Date(
        string='Date début',
        required=True,
        help="Date de début d'application de l'emploi du temps"
    )
    
    date_fin = fields.Date(
        string='Date fin',
        required=True,
        help="Date de fin d'application de l'emploi du temps"
    )
    
    ligne_ids = fields.One2many(
        'ensiasd.emploi.ligne',
        'emploi_id',
        string='Lignes de l\'emploi du temps'
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('active', 'Actif'),
        ('archived', 'Archivé'),
    ], string='État', default='draft', tracking=True)
    
    seance_ids = fields.One2many(
        'ensiasd.seance',
        'emploi_id',
        string='Séances générées'
    )
    
    seance_count = fields.Integer(
        string='Nb séances',
        compute='_compute_seance_count'
    )
    
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_emploi',
         'UNIQUE(filiere_id, semestre, annee_id)',
         'Un emploi du temps existe déjà pour cette filière/semestre/année!')
    ]

    @api.depends('filiere_id', 'semestre', 'annee_id')
    def _compute_name(self):
        for record in self:
            if record.filiere_id and record.semestre and record.annee_id:
                record.name = f"EDT {record.filiere_id.code} - {record.semestre} ({record.annee_id.name})"
            else:
                record.name = "Nouvel emploi du temps"

    @api.depends('seance_ids')
    def _compute_seance_count(self):
        for record in self:
            record.seance_count = len(record.seance_ids)

    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for record in self:
            if record.date_debut >= record.date_fin:
                raise ValidationError("La date de fin doit être après la date de début!")

    def action_confirm(self):
        """Confirmer l'emploi du temps"""
        self._check_conflicts()
        self.write({'state': 'confirmed'})

    def action_activate(self):
        """Activer l'emploi du temps"""
        self.write({'state': 'active'})

    def action_archive(self):
        """Archiver l'emploi du temps"""
        self.write({'state': 'archived'})

    def action_draft(self):
        """Remettre en brouillon"""
        self.write({'state': 'draft'})

    def _check_conflicts(self):
        """Vérifier les conflits dans l'emploi du temps"""
        for record in self:
            # Grouper par jour/créneau
            creneaux_used = {}
            for ligne in record.ligne_ids:
                key = (ligne.creneau_id.id, ligne.jour)
                if key not in creneaux_used:
                    creneaux_used[key] = []
                creneaux_used[key].append(ligne)
            
            # Vérifier conflits salle
            for key, lignes in creneaux_used.items():
                salles = [l.salle_id.id for l in lignes if l.salle_id]
                if len(salles) != len(set(salles)):
                    raise UserError("Conflit de salle détecté! Une salle est utilisée deux fois sur le même créneau.")
                
                # Vérifier conflits enseignant
                enseignants = [l.enseignant_id.id for l in lignes if l.enseignant_id]
                if len(enseignants) != len(set(enseignants)):
                    raise UserError("Conflit d'enseignant détecté! Un enseignant a deux cours sur le même créneau.")

    def action_generate_seances(self):
        """Ouvrir le wizard de génération des séances"""
        self.ensure_one()
        return {
            'name': 'Générer les séances',
            'type': 'ir.actions.act_window',
            'res_model': 'ensiasd.generate.seances.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_emploi_id': self.id,
                'default_date_debut': self.date_debut,
                'default_date_fin': self.date_fin,
            }
        }

    def action_view_seances(self):
        """Voir les séances générées"""
        self.ensure_one()
        return {
            'name': 'Séances',
            'type': 'ir.actions.act_window',
            'res_model': 'ensiasd.seance',
            'view_mode': 'calendar,tree,form',
            'domain': [('emploi_id', '=', self.id)],
            'context': {'default_emploi_id': self.id},
        }

    def generate_seances_for_period(self, date_debut, date_fin):
        """
        Générer toutes les séances pour la période donnée
        basé sur les lignes de l'emploi du temps
        """
        self.ensure_one()
        
        if self.state != 'active':
            raise UserError("L'emploi du temps doit être actif pour générer des séances!")
        
        Seance = self.env['ensiasd.seance']
        created_seances = self.env['ensiasd.seance']
        
        current_date = date_debut
        while current_date <= date_fin:
            # Jour de la semaine (0=lundi, 6=dimanche)
            weekday = str(current_date.weekday())
            
            # Trouver les lignes pour ce jour
            lignes = self.ligne_ids.filtered(lambda l: l.jour == weekday)
            
            for ligne in lignes:
                # Vérifier si la séance existe déjà
                existing = Seance.search([
                    ('emploi_id', '=', self.id),
                    ('element_id', '=', ligne.element_id.id),
                    ('date', '=', current_date),
                    ('heure_debut', '=', ligne.creneau_id.heure_debut),
                ], limit=1)
                
                if not existing:
                    # Créer la séance
                    seance = Seance.create({
                        'emploi_id': self.id,
                        'element_id': ligne.element_id.id,
                        'date': current_date,
                        'heure_debut': ligne.creneau_id.heure_debut,
                        'heure_fin': ligne.creneau_id.heure_fin,
                        'salle_id': ligne.salle_id.id,
                        'enseignant_id': ligne.enseignant_id.id or ligne.element_id.enseignant_id.id,
                        'groupe_ids': [(6, 0, ligne.groupe_ids.ids or self.groupe_ids.ids)],
                        'state': 'planned',
                    })
                    created_seances |= seance
            
            current_date += timedelta(days=1)
        
        return created_seances
