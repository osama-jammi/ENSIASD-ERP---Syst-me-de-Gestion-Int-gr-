# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdResultat(models.Model):
    """
    Résultat par semestre ou par année
    Agrège les notes des modules pour calculer les moyennes
    """
    _name = 'ensiasd.resultat'
    _description = 'Résultat académique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'annee_id desc, student_id, type_resultat'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True,
        tracking=True
    )
    
    filiere_id = fields.Many2one(
        'ensiasd.filiere',
        string='Filière',
        required=True
    )

    deliberation_id = fields.Many2one(
        'ensiasd.deliberation',
        string='Délibération',
        ondelete='set null'
    )

    type_resultat = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
        ('annee', 'Année complète'),
    ], string='Type', required=True, tracking=True)
    
    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session'
    )
    
    # Statistiques
    moyenne_generale = fields.Float(
        string='Moyenne générale',
        digits=(4, 2),
        compute='_compute_resultats',
        store=True
    )
    
    moyenne_ponderee = fields.Float(
        string='Moyenne pondérée',
        digits=(4, 2),
        compute='_compute_resultats',
        store=True
    )
    
    total_credits = fields.Integer(
        string='Crédits totaux',
        compute='_compute_resultats',
        store=True
    )
    
    credits_valides = fields.Integer(
        string='Crédits validés',
        compute='_compute_resultats',
        store=True
    )
    
    credits_non_valides = fields.Integer(
        string='Crédits non validés',
        compute='_compute_resultats',
        store=True
    )
    
    nb_modules = fields.Integer(
        string='Nombre de modules',
        compute='_compute_resultats',
        store=True
    )
    
    nb_modules_valides = fields.Integer(
        string='Modules validés',
        compute='_compute_resultats',
        store=True
    )
    
    nb_modules_non_valides = fields.Integer(
        string='Modules non validés',
        compute='_compute_resultats',
        store=True
    )
    
    nb_modules_rattrapage = fields.Integer(
        string='Modules en rattrapage',
        compute='_compute_resultats',
        store=True
    )
    
    # Décision
    decision = fields.Selection([
        ('en_cours', 'En cours'),
        ('admis', 'Admis'),
        ('admis_compensation', 'Admis par compensation'),
        ('ajourne', 'Ajourné'),
        ('redoublant', 'Redoublant'),
        ('exclus', 'Exclus'),
        ('rattrapage', 'Session de rattrapage'),
    ], string='Décision', default='en_cours', tracking=True)
    
    mention = fields.Selection([
        ('passable', 'Passable'),
        ('ab', 'Assez Bien'),
        ('bien', 'Bien'),
        ('tb', 'Très Bien'),
        ('excellent', 'Excellent'),
        ('honorable', 'Très Honorable'),
    ], string='Mention', compute='_compute_mention', store=True)
    
    rang = fields.Integer(string='Rang', default=0)
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('calculated', 'Calculé'),
        ('validated', 'Validé'),
        ('locked', 'Verrouillé'),
    ], string='État', default='draft', tracking=True)
    
    # Notes liées
    note_ids = fields.Many2many(
        'ensiasd.note',
        'resultat_note_rel',
        'resultat_id',
        'note_id',
        string='Notes',
        compute='_compute_notes',
        store=True
    )
    
    observations = fields.Text(string='Observations')
    decision_jury = fields.Text(string='Décision du jury')

    _sql_constraints = [
        ('unique_resultat',
         'UNIQUE(student_id, annee_id, type_resultat, session_id)',
         'Un résultat existe déjà pour cet étudiant, cette année et ce type!'),
    ]

    @api.depends('student_id', 'annee_id', 'type_resultat')
    def _compute_display_name(self):
        for record in self:
            if record.student_id and record.annee_id and record.type_resultat:
                type_label = dict(self._fields['type_resultat'].selection).get(record.type_resultat)
                record.display_name = f"{record.student_id.name} - {record.annee_id.name} - {type_label}"
            else:
                record.display_name = "Nouveau résultat"

    @api.depends('student_id', 'annee_id', 'type_resultat', 'filiere_id')
    def _compute_notes(self):
        """Récupérer les notes concernées"""
        for record in self:
            if not record.student_id or not record.annee_id or not record.type_resultat:
                record.note_ids = False
                continue
            
            domain = [
                ('student_id', '=', record.student_id.id),
                ('annee_id', '=', record.annee_id.id),
            ]
            
            if record.type_resultat != 'annee':
                domain.append(('semestre', '=', record.type_resultat))
            
            if record.filiere_id:
                domain.append(('filiere_id', '=', record.filiere_id.id))
            
            notes = self.env['ensiasd.note'].search(domain)
            record.note_ids = notes

    @api.depends('note_ids', 'note_ids.note_finale', 'note_ids.resultat',
                 'note_ids.module_id.credits_ects', 'note_ids.module_id.coefficient')
    def _compute_resultats(self):
        """Calculer les statistiques"""
        for record in self:
            notes = record.note_ids
            if not notes:
                record.moyenne_generale = 0.0
                record.moyenne_ponderee = 0.0
                record.total_credits = 0
                record.credits_valides = 0
                record.credits_non_valides = 0
                record.nb_modules = 0
                record.nb_modules_valides = 0
                record.nb_modules_non_valides = 0
                record.nb_modules_rattrapage = 0
                continue
            
            # Statistiques de base
            record.nb_modules = len(notes)
            record.nb_modules_valides = len(notes.filtered(lambda n: n.resultat == 'valide'))
            record.nb_modules_non_valides = len(notes.filtered(lambda n: n.resultat in ['non_valide', 'elimine']))
            record.nb_modules_rattrapage = len(notes.filtered(lambda n: n.resultat == 'rattrapage'))
            
            # Crédits
            record.total_credits = sum(notes.mapped('module_id.credits_ects'))
            record.credits_valides = sum(
                notes.filtered(lambda n: n.resultat in ['valide', 'compense']).mapped('module_id.credits_ects')
            )
            record.credits_non_valides = record.total_credits - record.credits_valides
            
            # Moyennes
            if notes:
                record.moyenne_generale = sum(notes.mapped('note_finale')) / len(notes)
                
                # Moyenne pondérée par coefficient
                total_coef = sum(notes.mapped('module_id.coefficient'))
                if total_coef > 0:
                    somme_ponderee = sum(
                        n.note_finale * n.module_id.coefficient for n in notes
                    )
                    record.moyenne_ponderee = somme_ponderee / total_coef
                else:
                    record.moyenne_ponderee = record.moyenne_generale

    @api.depends('moyenne_ponderee')
    def _compute_mention(self):
        """Calculer la mention"""
        for record in self:
            moyenne = record.moyenne_ponderee or 0
            if moyenne < 12:
                record.mention = 'passable'
            elif moyenne < 14:
                record.mention = 'ab'
            elif moyenne < 16:
                record.mention = 'bien'
            elif moyenne < 18:
                record.mention = 'tb'
            else:
                record.mention = 'excellent'

    def action_calculate(self):
        """Recalculer les résultats"""
        self._compute_notes()
        self._compute_resultats()
        self._compute_mention()
        self.write({'state': 'calculated'})

    def action_validate(self):
        """Valider le résultat"""
        self.write({'state': 'validated'})

    def action_lock(self):
        """Verrouiller le résultat"""
        self.write({'state': 'locked'})

    def action_reset_draft(self):
        """Remettre en brouillon"""
        for record in self:
            if record.state == 'locked':
                raise ValidationError(
                    "Impossible de modifier un résultat verrouillé!"
                )
        self.write({'state': 'draft'})

    def determine_decision(self):
        """Déterminer la décision automatique"""
        for record in self:
            config = self.env['ensiasd.config'].get_config()
            
            if record.nb_modules_non_valides == 0:
                record.decision = 'admis'
            elif record.moyenne_ponderee >= config.note_validation:
                # Compensation possible
                record.decision = 'admis_compensation'
            elif record.nb_modules_rattrapage > 0:
                record.decision = 'rattrapage'
            else:
                record.decision = 'ajourne'

    @api.model
    def generate_resultats_semestre(self, annee_id, semestre, filiere_id=None):
        """Générer les résultats pour un semestre"""
        domain = [
            ('annee_id', '=', annee_id),
            ('state', '=', 'validated'),
        ]
        if filiere_id:
            domain.append(('filiere_id', '=', filiere_id))
        
        inscriptions = self.env['ensiasd.inscription'].search(domain)
        students = inscriptions.mapped('student_id')
        
        resultats = self.env['ensiasd.resultat']
        for student in students:
            existing = self.search([
                ('student_id', '=', student.id),
                ('annee_id', '=', annee_id),
                ('type_resultat', '=', semestre),
            ], limit=1)
            
            if not existing:
                filiere = student.groupe_id.filiere_id if hasattr(student.groupe_id, 'filiere_id') else False
                resultat = self.create({
                    'student_id': student.id,
                    'annee_id': annee_id,
                    'type_resultat': semestre,
                    'filiere_id': filiere.id if filiere else filiere_id,
                })
                resultats |= resultat
            else:
                resultats |= existing
        
        resultats.action_calculate()
        return resultats

    def compute_ranking(self):
        """Calculer le classement"""
        # Grouper par filière et type
        groups = {}
        for record in self:
            key = (record.filiere_id.id, record.type_resultat, record.annee_id.id)
            if key not in groups:
                groups[key] = []
            groups[key].append(record)
        
        for key, resultats in groups.items():
            # Trier par moyenne pondérée décroissante
            sorted_resultats = sorted(resultats, key=lambda r: r.moyenne_ponderee, reverse=True)
            for i, resultat in enumerate(sorted_resultats, 1):
                resultat.rang = i
