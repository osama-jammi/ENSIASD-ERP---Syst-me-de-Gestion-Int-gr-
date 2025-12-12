# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdEmploiLigne(models.Model):
    """
    Ligne d'emploi du temps - association créneau/élément/salle
    """
    _name = 'ensiasd.emploi.ligne'
    _description = 'Ligne d\'emploi du temps'
    _order = 'jour, creneau_id'

    emploi_id = fields.Many2one(
        'ensiasd.emploi',
        string='Emploi du temps',
        required=True,
        ondelete='cascade'
    )
    
    jour = fields.Selection([
        ('0', 'Lundi'),
        ('1', 'Mardi'),
        ('2', 'Mercredi'),
        ('3', 'Jeudi'),
        ('4', 'Vendredi'),
        ('5', 'Samedi'),
    ], string='Jour', required=True)
    
    creneau_id = fields.Many2one(
        'ensiasd.creneau',
        string='Créneau',
        required=True,
        domain="[('jour', '=', jour)]"
    )
    
    element_id = fields.Many2one(
        'ensiasd.element',
        string='Élément',
        required=True,
        domain="[('module_id.filiere_id', '=', parent.filiere_id), ('module_id.semestre', '=', parent.semestre)]"
    )
    
    module_id = fields.Many2one(
        related='element_id.module_id',
        store=True,
        string='Module'
    )
    
    type_element = fields.Selection(
        related='element_id.type_element',
        store=True,
        string='Type'
    )
    
    salle_id = fields.Many2one(
        'ensiasd.salle',
        string='Salle',
        required=True
    )
    
    enseignant_id = fields.Many2one(
        'hr.employee',
        string='Enseignant',
        domain=[('is_enseignant', '=', True)],
        help="Laisser vide pour utiliser l'enseignant de l'élément"
    )
    
    groupe_ids = fields.Many2many(
        'ensiasd.groupe',
        'emploi_ligne_groupe_rel',
        'ligne_id',
        'groupe_id',
        string='Groupes',
        help="Laisser vide pour tous les groupes de l'emploi du temps"
    )
    
    frequence = fields.Selection([
        ('weekly', 'Chaque semaine'),
        ('biweekly_odd', 'Semaines impaires'),
        ('biweekly_even', 'Semaines paires'),
    ], string='Fréquence', default='weekly')
    
    color = fields.Integer(
        string='Couleur',
        compute='_compute_color'
    )
    
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('element_id', 'salle_id', 'creneau_id')
    def _compute_display_name(self):
        for record in self:
            if record.element_id and record.salle_id:
                record.display_name = f"{record.element_id.module_id.code} ({record.element_id.type_element.upper()}) - {record.salle_id.name}"
            else:
                record.display_name = "Nouvelle ligne"

    @api.depends('element_id.type_element')
    def _compute_color(self):
        colors = {'cm': 1, 'td': 2, 'tp': 3}
        for record in self:
            record.color = colors.get(record.element_id.type_element, 0) if record.element_id else 0

    @api.constrains('creneau_id', 'jour')
    def _check_creneau_jour(self):
        for record in self:
            if record.creneau_id and record.creneau_id.jour != record.jour:
                raise ValidationError("Le créneau sélectionné ne correspond pas au jour!")

    @api.constrains('salle_id', 'creneau_id', 'jour', 'emploi_id')
    def _check_salle_disponible(self):
        """Vérifier que la salle n'est pas déjà occupée"""
        for record in self:
            conflits = self.search([
                ('id', '!=', record.id),
                ('salle_id', '=', record.salle_id.id),
                ('creneau_id', '=', record.creneau_id.id),
                ('jour', '=', record.jour),
                ('emploi_id.annee_id', '=', record.emploi_id.annee_id.id),
                ('emploi_id.state', 'in', ['confirmed', 'active']),
            ])
            if conflits:
                raise ValidationError(
                    f"La salle {record.salle_id.name} est déjà occupée sur ce créneau "
                    f"par {conflits[0].emploi_id.name}!"
                )

    @api.constrains('enseignant_id', 'creneau_id', 'jour', 'emploi_id')
    def _check_enseignant_disponible(self):
        """Vérifier que l'enseignant n'a pas de conflit"""
        for record in self:
            if not record.enseignant_id:
                continue
            
            # Vérifier indisponibilités
            indispo = self.env['ensiasd.indisponibilite'].search([
                ('enseignant_id', '=', record.enseignant_id.id),
                ('jour', '=', record.jour),
                ('type_indispo', '=', 'recurring'),
            ])
            for ind in indispo:
                if (record.creneau_id.heure_debut < ind.heure_fin and 
                    record.creneau_id.heure_fin > ind.heure_debut):
                    raise ValidationError(
                        f"L'enseignant {record.enseignant_id.name} est indisponible sur ce créneau!"
                    )
            
            # Vérifier conflits avec autres cours
            conflits = self.search([
                ('id', '!=', record.id),
                ('enseignant_id', '=', record.enseignant_id.id),
                ('creneau_id', '=', record.creneau_id.id),
                ('jour', '=', record.jour),
                ('emploi_id.annee_id', '=', record.emploi_id.annee_id.id),
                ('emploi_id.state', 'in', ['confirmed', 'active']),
            ])
            if conflits:
                raise ValidationError(
                    f"L'enseignant {record.enseignant_id.name} a déjà un cours sur ce créneau "
                    f"({conflits[0].emploi_id.name})!"
                )

    @api.onchange('element_id')
    def _onchange_element_id(self):
        """Pré-remplir l'enseignant de l'élément"""
        if self.element_id and self.element_id.enseignant_id:
            self.enseignant_id = self.element_id.enseignant_id

    @api.onchange('jour')
    def _onchange_jour(self):
        """Réinitialiser le créneau si le jour change"""
        if self.creneau_id and self.creneau_id.jour != self.jour:
            self.creneau_id = False
