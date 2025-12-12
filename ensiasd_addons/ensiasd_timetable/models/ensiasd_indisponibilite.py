# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdIndisponibilite(models.Model):
    """
    Indisponibilités des enseignants et salles
    """
    _name = 'ensiasd.indisponibilite'
    _description = 'Indisponibilité'
    _order = 'date_debut desc, enseignant_id'

    name = fields.Char(string='Motif', required=True)
    
    type_ressource = fields.Selection([
        ('enseignant', 'Enseignant'),
        ('salle', 'Salle'),
    ], string='Type', required=True, default='enseignant')
    
    enseignant_id = fields.Many2one(
        'hr.employee',
        string='Enseignant',
        domain=[('is_enseignant', '=', True)]
    )
    
    salle_id = fields.Many2one(
        'ensiasd.salle',
        string='Salle'
    )
    
    type_indispo = fields.Selection([
        ('recurring', 'Récurrente (chaque semaine)'),
        ('ponctuelle', 'Ponctuelle (dates précises)'),
    ], string='Type d\'indisponibilité', required=True, default='ponctuelle')
    
    # Pour indisponibilité récurrente
    jour = fields.Selection([
        ('0', 'Lundi'),
        ('1', 'Mardi'),
        ('2', 'Mercredi'),
        ('3', 'Jeudi'),
        ('4', 'Vendredi'),
        ('5', 'Samedi'),
    ], string='Jour')
    
    heure_debut = fields.Float(string='Heure début')
    heure_fin = fields.Float(string='Heure fin')
    
    # Pour indisponibilité ponctuelle
    date_debut = fields.Date(string='Date début')
    date_fin = fields.Date(string='Date fin')
    journee_complete = fields.Boolean(
        string='Journée complète',
        default=True
    )
    
    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique'
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
    ], string='État', default='draft')
    
    notes = fields.Text(string='Notes')

    @api.constrains('type_ressource', 'enseignant_id', 'salle_id')
    def _check_ressource(self):
        for record in self:
            if record.type_ressource == 'enseignant' and not record.enseignant_id:
                raise ValidationError("Veuillez sélectionner un enseignant!")
            if record.type_ressource == 'salle' and not record.salle_id:
                raise ValidationError("Veuillez sélectionner une salle!")

    @api.constrains('type_indispo', 'jour', 'date_debut', 'date_fin')
    def _check_type_indispo(self):
        for record in self:
            if record.type_indispo == 'recurring' and not record.jour:
                raise ValidationError("Veuillez sélectionner un jour pour une indisponibilité récurrente!")
            if record.type_indispo == 'ponctuelle':
                if not record.date_debut:
                    raise ValidationError("Veuillez indiquer la date de début!")
                if record.date_fin and record.date_debut > record.date_fin:
                    raise ValidationError("La date de fin doit être après la date de début!")

    @api.constrains('heure_debut', 'heure_fin')
    def _check_heures(self):
        for record in self:
            if record.type_indispo == 'recurring' or not record.journee_complete:
                if record.heure_debut and record.heure_fin and record.heure_debut >= record.heure_fin:
                    raise ValidationError("L'heure de fin doit être après l'heure de début!")

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def is_indispo_for_date(self, date, heure_debut=None, heure_fin=None):
        """
        Vérifier si l'indisponibilité s'applique à une date/heure donnée
        """
        self.ensure_one()
        
        if self.state != 'confirmed':
            return False
        
        if self.type_indispo == 'ponctuelle':
            # Vérifier la date
            if self.date_debut and date < self.date_debut:
                return False
            if self.date_fin and date > self.date_fin:
                return False
            
            # Si journée complète, indispo
            if self.journee_complete:
                return True
            
            # Sinon vérifier les heures
            if heure_debut and heure_fin:
                if self.heure_debut and self.heure_fin:
                    return (heure_debut < self.heure_fin and heure_fin > self.heure_debut)
            return True
        
        else:  # recurring
            # Vérifier le jour de la semaine
            if str(date.weekday()) != self.jour:
                return False
            
            # Vérifier l'année académique si spécifiée
            if self.annee_id:
                if date < self.annee_id.date_debut or date > self.annee_id.date_fin:
                    return False
            
            # Vérifier les heures si spécifiées
            if heure_debut and heure_fin and self.heure_debut and self.heure_fin:
                return (heure_debut < self.heure_fin and heure_fin > self.heure_debut)
            
            return True
