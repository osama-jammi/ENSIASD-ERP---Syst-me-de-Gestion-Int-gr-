# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta


class GenerateSeancesWizard(models.TransientModel):
    """
    Wizard pour générer les séances à partir d'un emploi du temps
    """
    _name = 'ensiasd.generate.seances.wizard'
    _description = 'Générateur de séances'

    emploi_id = fields.Many2one(
        'ensiasd.emploi',
        string='Emploi du temps',
        required=True
    )
    
    date_debut = fields.Date(
        string='Date début',
        required=True
    )
    
    date_fin = fields.Date(
        string='Date fin',
        required=True
    )
    
    exclure_vacances = fields.Boolean(
        string='Exclure les vacances',
        default=True
    )
    
    envoyer_notifications = fields.Boolean(
        string='Notifier les enseignants',
        default=True,
        help="Envoyer un email aux enseignants pour les informer des séances planifiées"
    )
    
    # Résultat
    seances_count = fields.Integer(
        string='Séances générées',
        readonly=True
    )
    
    state = fields.Selection([
        ('config', 'Configuration'),
        ('done', 'Terminé'),
    ], default='config')

    @api.onchange('emploi_id')
    def _onchange_emploi_id(self):
        if self.emploi_id:
            self.date_debut = self.emploi_id.date_debut
            self.date_fin = self.emploi_id.date_fin

    def action_generate(self):
        """Générer les séances"""
        self.ensure_one()
        
        if not self.emploi_id:
            raise UserError("Veuillez sélectionner un emploi du temps!")
        
        if self.emploi_id.state not in ['confirmed', 'active']:
            raise UserError("L'emploi du temps doit être confirmé ou actif!")
        
        if not self.emploi_id.ligne_ids:
            raise UserError("L'emploi du temps n'a aucune ligne!")
        
        # Générer les séances
        seances = self._generate_seances()
        
        self.seances_count = len(seances)
        self.state = 'done'
        
        # Envoyer notifications si demandé
        if self.envoyer_notifications and seances:
            self._send_notifications(seances)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _generate_seances(self):
        """Générer les séances pour la période"""
        Seance = self.env['ensiasd.seance']
        created_seances = self.env['ensiasd.seance']
        
        current_date = self.date_debut
        while current_date <= self.date_fin:
            # Jour de la semaine (0=lundi)
            weekday = str(current_date.weekday())
            
            # Vérifier si c'est un jour de vacances
            if self.exclure_vacances and self._is_vacation_day(current_date):
                current_date += timedelta(days=1)
                continue
            
            # Trouver les lignes pour ce jour
            lignes = self.emploi_id.ligne_ids.filtered(lambda l: l.jour == weekday)
            
            for ligne in lignes:
                # Vérifier la fréquence
                if not self._check_frequency(ligne, current_date):
                    continue
                
                # Vérifier indisponibilités ponctuelles
                if self._has_indisponibility(ligne, current_date):
                    continue
                
                # Vérifier si la séance existe déjà
                existing = Seance.search([
                    ('emploi_id', '=', self.emploi_id.id),
                    ('element_id', '=', ligne.element_id.id),
                    ('date', '=', current_date),
                    ('heure_debut', '=', ligne.creneau_id.heure_debut),
                ], limit=1)
                
                if not existing:
                    # Créer la séance
                    seance = Seance.create({
                        'emploi_id': self.emploi_id.id,
                        'emploi_ligne_id': ligne.id,
                        'element_id': ligne.element_id.id,
                        'date': current_date,
                        'heure_debut': ligne.creneau_id.heure_debut,
                        'heure_fin': ligne.creneau_id.heure_fin,
                        'salle_id': ligne.salle_id.id,
                        'enseignant_id': ligne.enseignant_id.id or ligne.element_id.enseignant_id.id,
                        'groupe_ids': [(6, 0, ligne.groupe_ids.ids)] if ligne.groupe_ids else 
                                     [(6, 0, self.emploi_id.groupe_ids.ids)] if self.emploi_id.groupe_ids else False,
                        'state': 'planned',
                        'is_generated': True,
                    })
                    created_seances |= seance
            
            current_date += timedelta(days=1)
        
        return created_seances

    def _check_frequency(self, ligne, date):
        """Vérifier si la séance doit avoir lieu selon la fréquence"""
        if ligne.frequence == 'weekly':
            return True
        
        # Numéro de semaine
        week_number = date.isocalendar()[1]
        
        if ligne.frequence == 'biweekly_odd':
            return week_number % 2 == 1
        elif ligne.frequence == 'biweekly_even':
            return week_number % 2 == 0
        
        return True

    def _is_vacation_day(self, date):
        """Vérifier si la date est un jour de vacances"""
        # Rechercher dans les périodes de vacances si elles existent
        # Pour l'instant, on vérifie juste les dimanches
        if date.weekday() == 6:  # Dimanche
            return True
        
        # TODO: Ajouter la gestion des périodes de vacances
        return False

    def _has_indisponibility(self, ligne, date):
        """Vérifier les indisponibilités ponctuelles"""
        Indispo = self.env['ensiasd.indisponibilite']
        
        # Vérifier indisponibilité enseignant
        enseignant_id = ligne.enseignant_id.id or (ligne.element_id.enseignant_id.id if ligne.element_id.enseignant_id else False)
        if enseignant_id:
            indispos = Indispo.search([
                ('enseignant_id', '=', enseignant_id),
                ('type_indispo', '=', 'ponctuelle'),
                ('date_debut', '<=', date),
                '|', ('date_fin', '>=', date), ('date_fin', '=', False),
                ('state', '=', 'confirmed'),
            ])
            for ind in indispos:
                if ind.is_indispo_for_date(date, ligne.creneau_id.heure_debut, ligne.creneau_id.heure_fin):
                    return True
        
        # Vérifier indisponibilité salle
        indispos_salle = Indispo.search([
            ('salle_id', '=', ligne.salle_id.id),
            ('type_indispo', '=', 'ponctuelle'),
            ('date_debut', '<=', date),
            '|', ('date_fin', '>=', date), ('date_fin', '=', False),
            ('state', '=', 'confirmed'),
        ])
        for ind in indispos_salle:
            if ind.is_indispo_for_date(date, ligne.creneau_id.heure_debut, ligne.creneau_id.heure_fin):
                return True
        
        return False

    def _send_notifications(self, seances):
        """Envoyer les notifications aux enseignants"""
        # Grouper les séances par enseignant
        seances_by_teacher = {}
        for seance in seances:
            if seance.enseignant_id:
                if seance.enseignant_id.id not in seances_by_teacher:
                    seances_by_teacher[seance.enseignant_id.id] = {
                        'enseignant': seance.enseignant_id,
                        'seances': []
                    }
                seances_by_teacher[seance.enseignant_id.id]['seances'].append(seance)
        
        # Envoyer un email à chaque enseignant
        template = self.env.ref('ensiasd_timetable.mail_template_seances_planifiees', raise_if_not_found=False)
        if template:
            for data in seances_by_teacher.values():
                # Créer un contexte avec les informations
                ctx = {
                    'enseignant': data['enseignant'],
                    'seances': data['seances'],
                    'nb_seances': len(data['seances']),
                }
                template.with_context(**ctx).send_mail(data['seances'][0].id, force_send=False)

    def action_view_seances(self):
        """Voir les séances générées"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ensiasd.seance',
            'view_mode': 'calendar,tree,form',
            'domain': [('emploi_id', '=', self.emploi_id.id)],
            'context': {'default_emploi_id': self.emploi_id.id},
        }
