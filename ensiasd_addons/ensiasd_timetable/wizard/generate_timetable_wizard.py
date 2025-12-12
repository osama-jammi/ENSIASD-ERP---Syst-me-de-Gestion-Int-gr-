# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import random


class GenerateTimetableWizard(models.TransientModel):
    """
    Wizard pour générer automatiquement un emploi du temps
    """
    _name = 'ensiasd.generate.timetable.wizard'
    _description = 'Générateur d\'emploi du temps'

    filiere_id = fields.Many2one(
        'ensiasd.filiere',
        string='Filière',
        required=True
    )
    
    semestre = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
    ], string='Semestre', required=True)
    
    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True,
        default=lambda self: self._default_annee()
    )
    
    date_debut = fields.Date(
        string='Date début',
        required=True
    )
    
    date_fin = fields.Date(
        string='Date fin',
        required=True
    )
    
    groupe_ids = fields.Many2many(
        'ensiasd.groupe',
        string='Groupes'
    )
    
    # Options de génération
    max_heures_jour = fields.Integer(
        string='Max heures/jour',
        default=8,
        help="Nombre maximum d'heures de cours par jour"
    )
    
    eviter_trous = fields.Boolean(
        string='Éviter les trous',
        default=True,
        help="Essayer de regrouper les cours sans trous"
    )
    
    priorite_tp = fields.Boolean(
        string='TP en après-midi',
        default=True,
        help="Placer les TP de préférence l'après-midi"
    )
    
    # Résultat
    emploi_id = fields.Many2one(
        'ensiasd.emploi',
        string='Emploi généré',
        readonly=True
    )
    
    state = fields.Selection([
        ('config', 'Configuration'),
        ('done', 'Terminé'),
    ], default='config')

    def _default_annee(self):
        config = self.env['ensiasd.config'].get_config()
        return config.annee_courante_id

    @api.onchange('annee_id')
    def _onchange_annee_id(self):
        if self.annee_id:
            self.date_debut = self.annee_id.date_debut
            self.date_fin = self.annee_id.date_fin

    def action_generate(self):
        """Générer l'emploi du temps automatiquement"""
        self.ensure_one()
        
        # Vérifier qu'il n'existe pas déjà
        existing = self.env['ensiasd.emploi'].search([
            ('filiere_id', '=', self.filiere_id.id),
            ('semestre', '=', self.semestre),
            ('annee_id', '=', self.annee_id.id),
        ], limit=1)
        
        if existing:
            raise UserError(
                f"Un emploi du temps existe déjà pour {self.filiere_id.name} - {self.semestre}. "
                "Veuillez le supprimer ou le modifier."
            )
        
        # Récupérer les modules du semestre
        modules = self.env['ensiasd.module'].search([
            ('filiere_id', '=', self.filiere_id.id),
            ('semestre', '=', self.semestre),
            ('active', '=', True),
        ])
        
        if not modules:
            raise UserError("Aucun module trouvé pour cette filière/semestre!")
        
        # Récupérer tous les éléments à planifier
        elements = modules.mapped('element_ids')
        if not elements:
            raise UserError("Aucun élément à planifier!")
        
        # Récupérer les créneaux disponibles
        creneaux = self.env['ensiasd.creneau'].search([('active', '=', True)])
        if not creneaux:
            raise UserError("Aucun créneau horaire défini!")
        
        # Récupérer les salles
        salles_cours = self.env['ensiasd.salle'].search([
            ('type_salle', 'in', ['amphi', 'salle_cours']),
            ('active', '=', True),
        ])
        salles_tp = self.env['ensiasd.salle'].search([
            ('type_salle', '=', 'labo'),
            ('active', '=', True),
        ])
        
        if not salles_cours:
            raise UserError("Aucune salle de cours disponible!")
        
        # Créer l'emploi du temps
        emploi = self.env['ensiasd.emploi'].create({
            'filiere_id': self.filiere_id.id,
            'semestre': self.semestre,
            'annee_id': self.annee_id.id,
            'date_debut': self.date_debut,
            'date_fin': self.date_fin,
            'groupe_ids': [(6, 0, self.groupe_ids.ids)] if self.groupe_ids else False,
        })
        
        # Générer les lignes
        lignes_created = []
        creneaux_utilises = {}  # {jour: [creneau_ids]}
        
        for element in elements:
            # Calculer le nombre de séances nécessaires par semaine
            # (volume horaire / 14 semaines environ)
            heures_semaine = element.volume_horaire / 14
            nb_seances = max(1, int(heures_semaine / 1.5))  # 1h30 par séance
            
            for _ in range(nb_seances):
                # Trouver un créneau libre
                creneau = self._find_available_slot(
                    element, 
                    creneaux, 
                    creneaux_utilises,
                    emploi
                )
                
                if not creneau:
                    continue  # Pas de créneau disponible
                
                # Trouver une salle
                if element.type_element == 'tp':
                    salle = self._find_available_room(
                        salles_tp, 
                        creneau, 
                        creneaux_utilises,
                        emploi
                    ) or self._find_available_room(salles_cours, creneau, creneaux_utilises, emploi)
                else:
                    salle = self._find_available_room(
                        salles_cours, 
                        creneau, 
                        creneaux_utilises,
                        emploi
                    )
                
                if not salle:
                    continue  # Pas de salle disponible
                
                # Créer la ligne
                ligne = self.env['ensiasd.emploi.ligne'].create({
                    'emploi_id': emploi.id,
                    'jour': creneau.jour,
                    'creneau_id': creneau.id,
                    'element_id': element.id,
                    'salle_id': salle.id,
                    'enseignant_id': element.enseignant_id.id if element.enseignant_id else False,
                })
                lignes_created.append(ligne)
                
                # Marquer le créneau comme utilisé
                key = (creneau.jour, creneau.id, salle.id)
                creneaux_utilises[key] = True
        
        self.emploi_id = emploi
        self.state = 'done'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _find_available_slot(self, element, creneaux, creneaux_utilises, emploi):
        """Trouver un créneau disponible pour l'élément"""
        # Filtrer par type
        if element.type_element == 'tp' and self.priorite_tp:
            # TP de préférence après 14h
            creneaux_filtered = creneaux.filtered(lambda c: c.heure_debut >= 14)
            if not creneaux_filtered:
                creneaux_filtered = creneaux
        else:
            creneaux_filtered = creneaux
        
        # Mélanger pour varier
        creneaux_list = list(creneaux_filtered)
        random.shuffle(creneaux_list)
        
        for creneau in creneaux_list:
            # Vérifier que le créneau n'est pas déjà pris par un autre cours du même emploi
            already_used = any(
                ligne.creneau_id.id == creneau.id and ligne.jour == creneau.jour
                for ligne in emploi.ligne_ids
            )
            if not already_used:
                # Vérifier l'enseignant
                if element.enseignant_id:
                    enseignant_libre = self._check_enseignant_disponible(
                        element.enseignant_id, 
                        creneau, 
                        emploi
                    )
                    if not enseignant_libre:
                        continue
                
                return creneau
        
        return None

    def _find_available_room(self, salles, creneau, creneaux_utilises, emploi):
        """Trouver une salle disponible pour le créneau"""
        for salle in salles:
            key = (creneau.jour, creneau.id, salle.id)
            if key not in creneaux_utilises:
                # Vérifier qu'aucune autre ligne n'utilise cette salle sur ce créneau
                conflict = self.env['ensiasd.emploi.ligne'].search([
                    ('salle_id', '=', salle.id),
                    ('creneau_id', '=', creneau.id),
                    ('jour', '=', creneau.jour),
                    ('emploi_id.annee_id', '=', emploi.annee_id.id),
                    ('emploi_id.state', 'in', ['confirmed', 'active']),
                ], limit=1)
                if not conflict:
                    return salle
        return None

    def _check_enseignant_disponible(self, enseignant, creneau, emploi):
        """Vérifier si l'enseignant est disponible"""
        # Vérifier les indisponibilités récurrentes
        indispos = self.env['ensiasd.indisponibilite'].search([
            ('enseignant_id', '=', enseignant.id),
            ('type_indispo', '=', 'recurring'),
            ('jour', '=', creneau.jour),
            ('state', '=', 'confirmed'),
        ])
        
        for ind in indispos:
            if ind.heure_debut and ind.heure_fin:
                if creneau.heure_debut < ind.heure_fin and creneau.heure_fin > ind.heure_debut:
                    return False
            else:
                return False  # Indispo toute la journée
        
        # Vérifier les conflits avec d'autres emplois du temps
        conflits = self.env['ensiasd.emploi.ligne'].search([
            ('enseignant_id', '=', enseignant.id),
            ('creneau_id', '=', creneau.id),
            ('jour', '=', creneau.jour),
            ('emploi_id.annee_id', '=', emploi.annee_id.id),
            ('emploi_id.state', 'in', ['confirmed', 'active']),
        ], limit=1)
        
        return not conflits

    def action_view_emploi(self):
        """Voir l'emploi du temps généré"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ensiasd.emploi',
            'res_id': self.emploi_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
