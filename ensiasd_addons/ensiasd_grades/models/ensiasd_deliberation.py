# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class EnsiasdDeliberation(models.Model):
    """
    Délibération du conseil de classe/jury
    Gère le processus de validation des résultats
    """
    _name = 'ensiasd.deliberation'
    _description = 'Délibération'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Référence',
        readonly=True,
        copy=False,
        default='Nouveau'
    )

    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True,
        tracking=True
    )

    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session',
        required=True,
        tracking=True
    )

    filiere_id = fields.Many2one(
        'ensiasd.filiere',
        string='Filière',
        required=True,
        tracking=True
    )

    type_deliberation = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
        ('annee', 'Fin d\'année'),
        ('diplome', 'Diplôme'),
    ], string='Type', required=True, tracking=True)

    date = fields.Datetime(
        string='Date de délibération',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )

    lieu = fields.Char(string='Lieu')

    # Jury
    president_id = fields.Many2one(
        'hr.employee',
        string='Président du jury',
        domain=[('is_enseignant', '=', True)]
    )

    membre_ids = fields.Many2many(
        'hr.employee',
        'deliberation_membre_rel',
        'deliberation_id',
        'employee_id',
        string='Membres du jury',
        domain=[('is_enseignant', '=', True)]
    )

    secretaire_id = fields.Many2one(
        'hr.employee',
        string='Secrétaire'
    )

    # RÃ©sultats concernÃ©s
    resultat_ids = fields.One2many(
        'ensiasd.resultat',
        'deliberation_id',
        string='RÃ©sultats'
    )

    # Notes liées (utiliser One2many avec le Many2one de ensiasd.note)
    note_ids = fields.One2many(
        'ensiasd.note',
        'deliberation_id',
        string='Notes',
        compute='_compute_notes',
        store=True
    )

    # Statistiques
    nb_etudiants = fields.Integer(
        string='Étudiants concernés',
        compute='_compute_statistics',
        store=True
    )

    nb_admis = fields.Integer(
        string='Admis',
        compute='_compute_statistics',
        store=True
    )

    nb_ajournes = fields.Integer(
        string='Ajournés',
        compute='_compute_statistics',
        store=True
    )

    nb_rattrapage = fields.Integer(
        string='En rattrapage',
        compute='_compute_statistics',
        store=True
    )

    taux_reussite = fields.Float(
        string='Taux de réussite (%)',
        compute='_compute_statistics',
        store=True
    )

    moyenne_promo = fields.Float(
        string='Moyenne de la promotion',
        compute='_compute_statistics',
        store=True,
        digits=(4, 2)
    )

    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('preparation', 'En préparation'),
        ('en_cours', 'En cours'),
        ('validated', 'Validée'),
        ('signed', 'Signée'),
        ('published', 'Publiée'),
    ], string='État', default='draft', tracking=True)

    pv_observations = fields.Text(string='Observations du PV')
    pv_decisions = fields.Text(string='Décisions particulières')

    # Dates importantes
    date_publication = fields.Datetime(string='Date de publication')
    date_signature = fields.Datetime(string='Date de signature')

    deliberation_line_ids = fields.One2many(
        'ensiasd.deliberation.line',
        'deliberation_id',
        string='Lignes de délibération'
    )

    # Validation
    validated_by = fields.Many2one('res.users', string='Validé par', readonly=True)
    validated_date = fields.Datetime(string='Date de validation', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('ensiasd.deliberation') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('resultat_ids', 'resultat_ids.note_ids')
    def _compute_notes(self):
        """Récupérer les notes liées aux résultats"""
        for record in self:
            notes = self.env['ensiasd.note']
            for resultat in record.resultat_ids:
                notes |= resultat.note_ids
            record.note_ids = notes

    @api.depends('resultat_ids', 'resultat_ids.decision', 'resultat_ids.moyenne_ponderee')
    def _compute_statistics(self):
        """Calculer les statistiques"""
        for record in self:
            resultats = record.resultat_ids
            if not resultats:
                record.nb_etudiants = 0
                record.nb_admis = 0
                record.nb_ajournes = 0
                record.nb_rattrapage = 0
                record.taux_reussite = 0.0
                record.moyenne_promo = 0.0
                continue

            record.nb_etudiants = len(resultats)
            record.nb_admis = len(resultats.filtered(
                lambda r: r.decision in ['admis', 'admis_compensation']
            ))
            record.nb_ajournes = len(resultats.filtered(
                lambda r: r.decision in ['ajourne', 'redoublant', 'exclus']
            ))
            record.nb_rattrapage = len(resultats.filtered(
                lambda r: r.decision == 'rattrapage'
            ))

            if record.nb_etudiants > 0:
                record.taux_reussite = (record.nb_admis / record.nb_etudiants) * 100
                record.moyenne_promo = sum(resultats.mapped('moyenne_ponderee')) / len(resultats)
            else:
                record.taux_reussite = 0.0
                record.moyenne_promo = 0.0

    def action_prepare(self):
        """Préparer la délibération"""
        self.ensure_one()
        self._load_resultats()
        self.write({'state': 'preparation'})

    def action_start(self):
        """Démarrer la délibération"""
        self.write({'state': 'en_cours'})

    def action_validate(self):
        """Valider la délibération"""
        self.ensure_one()

        # Vérifier que tous les résultats ont une décision
        for resultat in self.resultat_ids:
            if resultat.decision == 'en_cours':
                raise UserError(
                    f"Le résultat de {resultat.student_id.name} n'a pas de décision!"
                )

        # Verrouiller les notes et résultats
        self.note_ids.action_lock()
        self.resultat_ids.action_lock()

        self.write({
            'state': 'validated',
            'validated_by': self.env.uid,
            'validated_date': fields.Datetime.now(),
        })

    def action_sign(self):
        """Signer le PV de délibération"""
        self.write({
            'state': 'signed',
            'date_signature': fields.Datetime.now(),
        })

    def action_publish(self):
        """Publier les résultats"""
        self.write({
            'state': 'published',
            'date_publication': fields.Datetime.now(),
        })

    def action_reset_draft(self):
        """Remettre en brouillon"""
        if self.state in ['signed', 'published']:
            raise UserError(
                "Impossible de modifier une délibération signée ou publiée!"
            )
        self.write({'state': 'draft'})

    def _load_resultats(self):
        """Charger les résultats pour la délibération"""
        self.ensure_one()

        domain = [
            ('annee_id', '=', self.annee_id.id),
            ('filiere_id', '=', self.filiere_id.id),
            ('type_resultat', '=', self.type_deliberation),
        ]

        resultats = self.env['ensiasd.resultat'].search(domain)

        if not resultats:
            # Générer les résultats
            resultats = self.env['ensiasd.resultat'].generate_resultats_semestre(
                self.annee_id.id,
                self.type_deliberation,
                self.filiere_id.id
            )

        # Calculer les décisions automatiques
        resultats.determine_decision()

        # Calculer le classement
        resultats.compute_ranking()

        # Créer les lignes de délibération
        self.deliberation_line_ids.unlink()
        for resultat in resultats:
            self.env['ensiasd.deliberation.line'].create({
                'deliberation_id': self.id,
                'resultat_id': resultat.id,
                'student_id': resultat.student_id.id,
                'moyenne': resultat.moyenne_ponderee,
                'decision_auto': resultat.decision,
                'decision_finale': resultat.decision,
            })

        self.resultat_ids = resultats

    def action_generate_pv(self):
        """Générer le PV de délibération"""
        return self.env.ref('ensiasd_grades.action_report_pv_deliberation').report_action(self)

    def action_view_resultats(self):
        """Afficher les résultats"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Résultats',
            'res_model': 'ensiasd.resultat',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.resultat_ids.ids)],
            'context': {'default_annee_id': self.annee_id.id},
        }


class EnsiasdDeliberationLine(models.Model):
    """
    Ligne de délibération par étudiant
    Permet au jury de modifier les décisions individuellement
    """
    _name = 'ensiasd.deliberation.line'
    _description = 'Ligne de délibération'
    _order = 'rang, student_id'

    deliberation_id = fields.Many2one(
        'ensiasd.deliberation',
        string='Délibération',
        required=True,
        ondelete='cascade'
    )

    resultat_id = fields.Many2one(
        'ensiasd.resultat',
        string='Résultat',
        required=True
    )

    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        required=True
    )

    moyenne = fields.Float(
        string='Moyenne',
        digits=(4, 2)
    )

    rang = fields.Integer(
        related='resultat_id.rang',
        store=True
    )

    decision_auto = fields.Selection([
        ('en_cours', 'En cours'),
        ('admis', 'Admis'),
        ('admis_compensation', 'Admis par compensation'),
        ('ajourne', 'Ajourné'),
        ('redoublant', 'Redoublant'),
        ('exclus', 'Exclus'),
        ('rattrapage', 'Session de rattrapage'),
    ], string='Décision automatique', readonly=True)

    decision_finale = fields.Selection([
        ('en_cours', 'En cours'),
        ('admis', 'Admis'),
        ('admis_compensation', 'Admis par compensation'),
        ('ajourne', 'Ajourné'),
        ('redoublant', 'Redoublant'),
        ('exclus', 'Exclus'),
        ('rattrapage', 'Session de rattrapage'),
    ], string='Décision finale')

    observation = fields.Text(string='Observation')

    is_modified = fields.Boolean(
        string='Modifiée',
        compute='_compute_is_modified',
        store=True
    )

    @api.depends('decision_auto', 'decision_finale')
    def _compute_is_modified(self):
        for record in self:
            record.is_modified = record.decision_auto != record.decision_finale

    @api.onchange('decision_finale')
    def _onchange_decision_finale(self):
        """Synchroniser avec le résultat"""
        if self.resultat_id and self.decision_finale:
            self.resultat_id.decision = self.decision_finale