# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdBareme(models.Model):
    """
    Barème de notation configurable par module
    Définit les coefficients et pondérations des différentes évaluations
    """
    _name = 'ensiasd.bareme'
    _description = 'Barème de notation'
    _inherit = ['mail.thread']
    _order = 'module_id, name'

    name = fields.Char(string='Nom', required=True, tracking=True)
    
    module_id = fields.Many2one(
        'ensiasd.module',
        string='Module',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True
    )
    
    # Pondérations des différents types d'évaluation (en %)
    poids_cc = fields.Float(
        string='Poids CC (%)',
        default=30.0,
        help="Pourcentage du contrôle continu dans la note finale"
    )
    poids_examen = fields.Float(
        string='Poids Examen (%)',
        default=50.0,
        help="Pourcentage de l'examen final dans la note finale"
    )
    poids_tp = fields.Float(
        string='Poids TP (%)',
        default=20.0,
        help="Pourcentage des travaux pratiques dans la note finale"
    )
    poids_projet = fields.Float(
        string='Poids Projet (%)',
        default=0.0,
        help="Pourcentage du projet dans la note finale"
    )
    
    # Configuration spéciale
    nb_cc_prevu = fields.Integer(
        string='Nombre de CC prévus',
        default=2,
        help="Nombre de contrôles continus prévus"
    )
    
    meilleure_note_cc = fields.Boolean(
        string='Garder meilleure CC',
        default=False,
        help="Si activé, seule la meilleure note de CC est retenue"
    )
    
    note_eliminatoire = fields.Float(
        string='Note éliminatoire',
        default=6.0,
        help="Note en dessous de laquelle l'étudiant est éliminé"
    )
    
    note_validation = fields.Float(
        string='Note de validation',
        default=12.0,
        help="Note minimale pour valider le module"
    )
    
    rattrapage_autorise = fields.Boolean(
        string='Rattrapage autorisé',
        default=True
    )
    
    note_rattrapage_remplace = fields.Selection([
        ('examen', 'Remplace l\'examen uniquement'),
        ('total', 'Remplace la note totale'),
        ('meilleure', 'Garde la meilleure note'),
    ], string='Mode rattrapage', default='meilleure')
    
    bonus_max = fields.Float(
        string='Bonus maximum',
        default=2.0,
        help="Points bonus maximum pouvant être attribués"
    )
    
    active = fields.Boolean(default=True)
    observations = fields.Text(string='Observations')

    _sql_constraints = [
        ('module_annee_unique', 'UNIQUE(module_id, annee_id)',
         'Un barème existe déjà pour ce module et cette année!'),
    ]

    @api.constrains('poids_cc', 'poids_examen', 'poids_tp', 'poids_projet')
    def _check_poids_total(self):
        for record in self:
            total = record.poids_cc + record.poids_examen + record.poids_tp + record.poids_projet
            if abs(total - 100.0) > 0.01:
                raise ValidationError(
                    f"La somme des pondérations doit être égale à 100%! "
                    f"(Actuellement: {total}%)"
                )

    @api.constrains('note_eliminatoire', 'note_validation')
    def _check_notes_seuils(self):
        for record in self:
            config = self.env['ensiasd.config'].get_config()
            if record.note_eliminatoire < 0 or record.note_eliminatoire > config.note_max:
                raise ValidationError(
                    f"La note éliminatoire doit être entre 0 et {config.note_max}!"
                )
            if record.note_validation < 0 or record.note_validation > config.note_max:
                raise ValidationError(
                    f"La note de validation doit être entre 0 et {config.note_max}!"
                )
            if record.note_eliminatoire > record.note_validation:
                raise ValidationError(
                    "La note éliminatoire ne peut pas être supérieure à la note de validation!"
                )

    @api.model
    def get_bareme(self, module_id, annee_id):
        """Récupérer le barème d'un module pour une année donnée"""
        bareme = self.search([
            ('module_id', '=', module_id),
            ('annee_id', '=', annee_id),
        ], limit=1)
        
        if not bareme:
            # Créer un barème par défaut
            module = self.env['ensiasd.module'].browse(module_id)
            bareme = self.create({
                'name': f"Barème {module.code}",
                'module_id': module_id,
                'annee_id': annee_id,
            })
        return bareme

    def copy_to_next_year(self, new_annee_id):
        """Copier le barème pour une nouvelle année"""
        return self.copy({
            'annee_id': new_annee_id,
            'name': self.name,
        })


class EnsiasdBaremeLine(models.Model):
    """
    Ligne de barème pour les éléments de module
    Permet une configuration plus fine par élément
    """
    _name = 'ensiasd.bareme.line'
    _description = 'Ligne de barème par élément'
    _order = 'bareme_id, element_id'

    bareme_id = fields.Many2one(
        'ensiasd.bareme',
        string='Barème',
        required=True,
        ondelete='cascade'
    )
    
    element_id = fields.Many2one(
        'ensiasd.element',
        string='Élément',
        required=True,
        ondelete='cascade'
    )
    
    coefficient = fields.Float(
        string='Coefficient',
        default=1.0,
        required=True
    )
    
    poids_dans_module = fields.Float(
        string='Poids dans le module (%)',
        default=33.33
    )
    
    note_eliminatoire = fields.Float(
        string='Note éliminatoire',
        default=0.0
    )
