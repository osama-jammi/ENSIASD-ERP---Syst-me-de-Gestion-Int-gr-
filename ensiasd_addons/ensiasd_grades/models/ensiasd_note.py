# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdNote(models.Model):
    """
    Note par module - Calculée automatiquement à partir des notes par élément
    ou saisie directement pour les modules sans éléments
    """
    _name = 'ensiasd.note'
    _description = 'Note de module'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inscription_id, session_id'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    inscription_id = fields.Many2one(
        'ensiasd.inscription',
        string='Inscription',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    student_id = fields.Many2one(
        related='inscription_id.student_id',
        store=True,
        string='Étudiant'
    )
    
    module_id = fields.Many2one(
        related='inscription_id.module_id',
        store=True,
        string='Module'
    )
    
    filiere_id = fields.Many2one(
        related='module_id.filiere_id',
        store=True,
        string='Filière'
    )
    
    semestre = fields.Selection(
        related='module_id.semestre',
        store=True,
        string='Semestre'
    )
    
    annee_id = fields.Many2one(
        related='inscription_id.annee_id',
        store=True,
        string='Année'
    )
    
    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session',
        required=True,
        tracking=True
    )
    
    # Notes par type d'évaluation
    note_cc = fields.Float(
        string='Note CC',
        digits=(4, 2),
        compute='_compute_notes',
        store=True,
        readonly=False
    )
    
    note_tp = fields.Float(
        string='Note TP',
        digits=(4, 2),
        compute='_compute_notes',
        store=True,
        readonly=False
    )
    
    note_projet = fields.Float(
        string='Note Projet',
        digits=(4, 2),
        compute='_compute_notes',
        store=True,
        readonly=False
    )
    
    note_examen = fields.Float(
        string='Note Examen',
        digits=(4, 2),
        tracking=True
    )
    
    note_rattrapage = fields.Float(
        string='Note Rattrapage',
        digits=(4, 2),
        tracking=True
    )
    
    # Note finale calculée
    note_finale = fields.Float(
        string='Note finale',
        digits=(4, 2),
        compute='_compute_note_finale',
        store=True
    )
    
    note_finale_20 = fields.Float(
        string='Note /20',
        digits=(4, 2),
        compute='_compute_note_finale',
        store=True
    )
    
    # Bonus/Malus
    bonus = fields.Float(
        string='Bonus',
        digits=(4, 2),
        default=0.0
    )
    
    malus = fields.Float(
        string='Malus',
        digits=(4, 2),
        default=0.0
    )
    
    # Résultat
    resultat = fields.Selection([
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('non_valide', 'Non validé'),
        ('rattrapage', 'Rattrapage'),
        ('elimine', 'Éliminé'),
        ('compense', 'Compensé'),
        ('absent', 'Absent'),
    ], string='Résultat', compute='_compute_resultat', store=True)
    
    mention = fields.Selection([
        ('eliminatoire', 'Éliminatoire'),
        ('insuffisant', 'Insuffisant'),
        ('passable', 'Passable'),
        ('ab', 'Assez Bien'),
        ('bien', 'Bien'),
        ('tb', 'Très Bien'),
        ('excellent', 'Excellent'),
    ], string='Mention', compute='_compute_mention', store=True)
    
    # Absences
    nb_absences = fields.Integer(
        string='Absences',
        compute='_compute_absences',
        store=True
    )
    
    is_absent_examen = fields.Boolean(
        string='Absent à l\'examen',
        default=False
    )
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('validated', 'Validée'),
        ('deliberation', 'En délibération'),
        ('locked', 'Verrouillée'),
    ], string='État', default='draft', tracking=True)
    
    # Notes éléments liées
    note_element_ids = fields.One2many(
        'ensiasd.note.element',
        'inscription_id',
        string='Notes par élément',
        domain="[('inscription_id', '=', inscription_id)]"
    )
    
    observations = fields.Text(string='Observations')
    
    # Pour délibération
    deliberation_id = fields.Many2one(
        'ensiasd.deliberation',
        string='Délibération'
    )
    
    decision_jury = fields.Text(string='Décision du jury')

    _sql_constraints = [
        ('unique_note_module',
         'UNIQUE(inscription_id, session_id)',
         'Une note existe déjà pour cette inscription et cette session!'),
    ]

    @api.depends('student_id', 'module_id')
    def _compute_display_name(self):
        for record in self:
            if record.student_id and record.module_id:
                record.display_name = f"{record.student_id.name} - {record.module_id.code}"
            else:
                record.display_name = "Nouvelle note"

    @api.depends('note_element_ids', 'note_element_ids.valeur', 'note_element_ids.type_eval')
    def _compute_notes(self):
        """Calculer les notes par type à partir des notes éléments"""
        for record in self:
            elements = record.note_element_ids
            
            # Note CC (moyenne des CC)
            cc_notes = elements.filtered(lambda n: n.type_eval in ['cc1', 'cc2', 'cc3'])
            if cc_notes:
                record.note_cc = sum(cc_notes.mapped('valeur')) / len(cc_notes)
            
            # Note TP
            tp_notes = elements.filtered(lambda n: n.type_eval == 'tp')
            if tp_notes:
                record.note_tp = sum(tp_notes.mapped('valeur')) / len(tp_notes)
            
            # Note Projet
            projet_notes = elements.filtered(lambda n: n.type_eval == 'projet')
            if projet_notes:
                record.note_projet = sum(projet_notes.mapped('valeur')) / len(projet_notes)

    @api.depends('note_cc', 'note_tp', 'note_projet', 'note_examen', 
                 'note_rattrapage', 'bonus', 'malus', 'session_id', 'module_id', 'annee_id')
    def _compute_note_finale(self):
        """Calculer la note finale selon le barème"""
        for record in self:
            if not record.module_id or not record.annee_id:
                record.note_finale = 0.0
                record.note_finale_20 = 0.0
                continue
            
            # Récupérer le barème
            bareme = self.env['ensiasd.bareme'].get_bareme(
                record.module_id.id,
                record.annee_id.id
            )
            
            # Calcul pondéré
            note = 0.0
            if bareme.poids_cc > 0 and record.note_cc:
                note += (record.note_cc * bareme.poids_cc / 100)
            if bareme.poids_tp > 0 and record.note_tp:
                note += (record.note_tp * bareme.poids_tp / 100)
            if bareme.poids_projet > 0 and record.note_projet:
                note += (record.note_projet * bareme.poids_projet / 100)
            if bareme.poids_examen > 0:
                # Gérer le rattrapage
                note_exam = record.note_examen or 0.0
                if record.note_rattrapage:
                    if bareme.note_rattrapage_remplace == 'examen':
                        note_exam = record.note_rattrapage
                    elif bareme.note_rattrapage_remplace == 'meilleure':
                        note_exam = max(note_exam, record.note_rattrapage)
                    elif bareme.note_rattrapage_remplace == 'total':
                        # Le rattrapage remplace tout
                        note = record.note_rattrapage
                
                if bareme.note_rattrapage_remplace != 'total':
                    note += (note_exam * bareme.poids_examen / 100)
            
            # Appliquer bonus/malus
            note = note + record.bonus - record.malus
            
            # Limiter au maximum
            config = self.env['ensiasd.config'].get_config()
            note = min(max(0, note), config.note_max)
            
            record.note_finale = note
            record.note_finale_20 = note  # Déjà sur 20

    @api.depends('note_finale', 'module_id', 'annee_id', 'is_absent_examen')
    def _compute_resultat(self):
        """Déterminer le résultat (validé, non validé, etc.)"""
        for record in self:
            if record.is_absent_examen and not record.note_rattrapage:
                record.resultat = 'absent'
                continue
            
            if not record.module_id or not record.annee_id:
                record.resultat = 'en_cours'
                continue
            
            bareme = self.env['ensiasd.bareme'].get_bareme(
                record.module_id.id,
                record.annee_id.id
            )
            
            if record.note_finale < bareme.note_eliminatoire:
                record.resultat = 'elimine'
            elif record.note_finale >= bareme.note_validation:
                record.resultat = 'valide'
            elif record.note_finale >= bareme.note_eliminatoire:
                # Entre éliminatoire et validation
                if record.session_id and record.session_id.type_session == 'normale':
                    record.resultat = 'rattrapage'
                else:
                    record.resultat = 'non_valide'
            else:
                record.resultat = 'en_cours'

    @api.depends('note_finale')
    def _compute_mention(self):
        """Calculer la mention"""
        for record in self:
            note = record.note_finale or 0
            if note < 6:
                record.mention = 'eliminatoire'
            elif note < 10:
                record.mention = 'insuffisant'
            elif note < 12:
                record.mention = 'passable'
            elif note < 14:
                record.mention = 'ab'
            elif note < 16:
                record.mention = 'bien'
            elif note < 18:
                record.mention = 'tb'
            else:
                record.mention = 'excellent'

    @api.depends('note_element_ids', 'note_element_ids.is_absent')
    def _compute_absences(self):
        """Compter les absences"""
        for record in self:
            record.nb_absences = len(record.note_element_ids.filtered('is_absent'))

    @api.constrains('note_cc', 'note_tp', 'note_projet', 'note_examen', 'note_rattrapage')
    def _check_notes(self):
        """Vérifier que les notes sont dans les limites"""
        config = self.env['ensiasd.config'].get_config()
        for record in self:
            for field in ['note_cc', 'note_tp', 'note_projet', 'note_examen', 'note_rattrapage']:
                value = getattr(record, field) or 0
                if value < 0 or value > config.note_max:
                    raise ValidationError(
                        f"La note doit être comprise entre 0 et {config.note_max}!"
                    )

    def action_confirm(self):
        """Confirmer les notes"""
        self.write({'state': 'confirmed'})

    def action_validate(self):
        """Valider les notes"""
        self.write({'state': 'validated'})

    def action_deliberation(self):
        """Mettre en délibération"""
        self.write({'state': 'deliberation'})

    def action_lock(self):
        """Verrouiller après délibération"""
        self.write({'state': 'locked'})

    def action_reset_draft(self):
        """Remettre en brouillon"""
        for record in self:
            if record.state == 'locked':
                raise ValidationError(
                    "Impossible de modifier une note verrouillée après délibération!"
                )
        self.write({'state': 'draft'})

    def action_recalculate(self):
        """Forcer le recalcul des notes"""
        self._compute_notes()
        self._compute_note_finale()
        self._compute_resultat()
        self._compute_mention()
