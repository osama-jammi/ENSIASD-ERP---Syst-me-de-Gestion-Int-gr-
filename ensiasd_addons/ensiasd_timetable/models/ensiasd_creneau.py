# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdCreneau(models.Model):
    """
    Définition des créneaux horaires disponibles dans la semaine
    """
    _name = 'ensiasd.creneau'
    _description = 'Créneau horaire'
    _order = 'jour, heure_debut'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    
    jour = fields.Selection([
        ('0', 'Lundi'),
        ('1', 'Mardi'),
        ('2', 'Mercredi'),
        ('3', 'Jeudi'),
        ('4', 'Vendredi'),
        ('5', 'Samedi'),
    ], string='Jour', required=True)
    
    heure_debut = fields.Float(string='Heure début', required=True)
    heure_fin = fields.Float(string='Heure fin', required=True)
    
    type_creneau = fields.Selection([
        ('cours', 'Cours (CM/TD)'),
        ('tp', 'Travaux Pratiques'),
        ('all', 'Tous types'),
    ], string='Type de séance', default='all')
    
    duree = fields.Float(string='Durée (h)', compute='_compute_duree', store=True)
    active = fields.Boolean(default=True)
    
    # Pour identifier facilement le créneau
    code = fields.Char(string='Code', compute='_compute_code', store=True)

    @api.depends('jour', 'heure_debut', 'heure_fin')
    def _compute_name(self):
        jours = {'0': 'Lun', '1': 'Mar', '2': 'Mer', '3': 'Jeu', '4': 'Ven', '5': 'Sam'}
        for record in self:
            if record.jour and record.heure_debut and record.heure_fin:
                h_deb = f"{int(record.heure_debut):02d}:{int((record.heure_debut % 1) * 60):02d}"
                h_fin = f"{int(record.heure_fin):02d}:{int((record.heure_fin % 1) * 60):02d}"
                record.name = f"{jours.get(record.jour, '')} {h_deb}-{h_fin}"
            else:
                record.name = "Nouveau créneau"

    @api.depends('jour', 'heure_debut')
    def _compute_code(self):
        for record in self:
            record.code = f"{record.jour}_{int(record.heure_debut * 100)}"

    @api.depends('heure_debut', 'heure_fin')
    def _compute_duree(self):
        for record in self:
            record.duree = record.heure_fin - record.heure_debut

    @api.constrains('heure_debut', 'heure_fin')
    def _check_heures(self):
        for record in self:
            if record.heure_debut >= record.heure_fin:
                raise ValidationError("L'heure de fin doit être supérieure à l'heure de début!")
            if record.heure_debut < 8 or record.heure_fin > 20:
                raise ValidationError("Les heures doivent être entre 8h et 20h!")

    @staticmethod
    def float_to_time(float_hour):
        """Convertir une heure float en string HH:MM"""
        hours = int(float_hour)
        minutes = int((float_hour % 1) * 60)
        return f"{hours:02d}:{minutes:02d}"
