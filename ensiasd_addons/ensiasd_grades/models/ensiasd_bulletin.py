# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class EnsiasdBulletin(models.Model):
    """
    Bulletin de notes
    Document officiel récapitulatif des notes d'un étudiant
    """
    _name = 'ensiasd.bulletin'
    _description = 'Bulletin de notes'
    _inherit = ['mail.thread']
    _order = 'date_generation desc, student_id'

    name = fields.Char(
        string='Référence',
        readonly=True,
        copy=False,
        compute='_compute_name',
        store=True
    )
    
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
    
    type_bulletin = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
        ('annuel', 'Annuel'),
    ], string='Type', required=True, tracking=True)
    
    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session'
    )
    
    date_generation = fields.Datetime(
        string='Date de génération',
        default=fields.Datetime.now
    )
    
    # Informations étudiant
    student_cne = fields.Char(related='student_id.cne', string='CNE')
    student_matricule = fields.Char(related='student_id.matricule', string='Matricule')
    student_niveau = fields.Selection(related='student_id.niveau', string='Niveau')
    student_groupe = fields.Many2one(related='student_id.groupe_id', string='Groupe')
    
    # Résultat lié
    resultat_id = fields.Many2one(
        'ensiasd.resultat',
        string='Résultat',
        compute='_compute_resultat',
        store=True
    )
    
    # Lignes de bulletin
    line_ids = fields.One2many(
        'ensiasd.bulletin.line',
        'bulletin_id',
        string='Lignes',
        compute='_compute_lines',
        store=True
    )
    
    # Totaux
    moyenne_generale = fields.Float(
        string='Moyenne générale',
        digits=(4, 2),
        compute='_compute_totaux',
        store=True
    )
    
    moyenne_ponderee = fields.Float(
        string='Moyenne pondérée',
        digits=(4, 2),
        compute='_compute_totaux',
        store=True
    )
    
    total_credits = fields.Integer(
        string='Crédits totaux',
        compute='_compute_totaux',
        store=True
    )
    
    credits_valides = fields.Integer(
        string='Crédits validés',
        compute='_compute_totaux',
        store=True
    )
    
    mention = fields.Selection([
        ('passable', 'Passable'),
        ('ab', 'Assez Bien'),
        ('bien', 'Bien'),
        ('tb', 'Très Bien'),
        ('excellent', 'Excellent'),
    ], string='Mention', compute='_compute_mention', store=True)
    
    rang = fields.Integer(string='Rang')
    effectif = fields.Integer(string='Effectif promotion')
    
    decision = fields.Selection([
        ('en_cours', 'En cours'),
        ('admis', 'Admis'),
        ('admis_compensation', 'Admis par compensation'),
        ('ajourne', 'Ajourné'),
        ('rattrapage', 'Session de rattrapage'),
    ], string='Décision')
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('generated', 'Généré'),
        ('validated', 'Validé'),
        ('printed', 'Imprimé'),
    ], string='État', default='draft', tracking=True)
    
    observations = fields.Text(string='Observations')
    
    # Signature
    signed_by = fields.Many2one('hr.employee', string='Signé par')
    signature_date = fields.Date(string='Date de signature')

    _sql_constraints = [
        ('unique_bulletin',
         'UNIQUE(student_id, annee_id, type_bulletin, session_id)',
         'Un bulletin existe déjà pour cet étudiant, cette année et ce type!'),
    ]

    @api.depends('student_id', 'annee_id', 'type_bulletin')
    def _compute_name(self):
        for record in self:
            if record.student_id and record.annee_id and record.type_bulletin:
                type_label = dict(self._fields['type_bulletin'].selection).get(record.type_bulletin)
                record.name = f"BUL-{record.student_id.matricule or record.student_id.cne}-{record.annee_id.name.replace('/', '')}-{type_label}"
            else:
                record.name = "Nouveau"

    @api.depends('student_id', 'annee_id', 'type_bulletin')
    def _compute_resultat(self):
        """Trouver le résultat correspondant"""
        for record in self:
            if not all([record.student_id, record.annee_id, record.type_bulletin]):
                record.resultat_id = False
                continue
            
            type_res = record.type_bulletin if record.type_bulletin != 'annuel' else 'annee'
            resultat = self.env['ensiasd.resultat'].search([
                ('student_id', '=', record.student_id.id),
                ('annee_id', '=', record.annee_id.id),
                ('type_resultat', '=', type_res),
            ], limit=1)
            record.resultat_id = resultat

    @api.depends('student_id', 'annee_id', 'type_bulletin', 'filiere_id')
    def _compute_lines(self):
        """Générer les lignes du bulletin"""
        for record in self:
            if not all([record.student_id, record.annee_id, record.type_bulletin]):
                continue
            
            # Supprimer les anciennes lignes
            record.line_ids.unlink()
            
            # Rechercher les notes
            domain = [
                ('student_id', '=', record.student_id.id),
                ('annee_id', '=', record.annee_id.id),
            ]
            
            if record.type_bulletin != 'annuel':
                domain.append(('semestre', '=', record.type_bulletin))
            
            if record.filiere_id:
                domain.append(('filiere_id', '=', record.filiere_id.id))
            
            notes = self.env['ensiasd.note'].search(domain)
            
            lines = []
            for note in notes:
                lines.append((0, 0, {
                    'bulletin_id': record.id,
                    'note_id': note.id,
                    'module_id': note.module_id.id,
                    'note_cc': note.note_cc,
                    'note_tp': note.note_tp,
                    'note_examen': note.note_examen,
                    'note_rattrapage': note.note_rattrapage,
                    'note_finale': note.note_finale,
                    'credits': note.module_id.credits_ects,
                    'coefficient': note.module_id.coefficient,
                    'resultat': note.resultat,
                }))
            
            record.line_ids = lines

    @api.depends('line_ids', 'line_ids.note_finale', 'line_ids.credits', 'line_ids.coefficient')
    def _compute_totaux(self):
        """Calculer les totaux"""
        for record in self:
            lines = record.line_ids
            if not lines:
                record.moyenne_generale = 0.0
                record.moyenne_ponderee = 0.0
                record.total_credits = 0
                record.credits_valides = 0
                continue
            
            # Moyenne simple
            record.moyenne_generale = sum(lines.mapped('note_finale')) / len(lines)
            
            # Moyenne pondérée
            total_coef = sum(lines.mapped('coefficient'))
            if total_coef > 0:
                somme_ponderee = sum(l.note_finale * l.coefficient for l in lines)
                record.moyenne_ponderee = somme_ponderee / total_coef
            else:
                record.moyenne_ponderee = record.moyenne_generale
            
            # Crédits
            record.total_credits = sum(lines.mapped('credits'))
            record.credits_valides = sum(
                l.credits for l in lines if l.resultat in ['valide', 'compense']
            )

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

    def action_generate(self):
        """Générer le bulletin"""
        self._compute_resultat()
        self._compute_lines()
        self._compute_totaux()
        self._compute_mention()
        
        # Récupérer la décision du résultat
        if self.resultat_id:
            self.decision = self.resultat_id.decision
            self.rang = self.resultat_id.rang
        
        self.write({
            'state': 'generated',
            'date_generation': fields.Datetime.now(),
        })

    def action_validate(self):
        """Valider le bulletin"""
        self.write({'state': 'validated'})

    def action_print(self):
        """Imprimer le bulletin"""
        self.write({'state': 'printed'})
        return self.env.ref('ensiasd_grades.action_report_bulletin').report_action(self)

    def action_reset_draft(self):
        """Remettre en brouillon"""
        self.write({'state': 'draft'})

    @api.model
    def generate_bulletins_batch(self, annee_id, type_bulletin, filiere_id=None):
        """Générer les bulletins en lot"""
        domain = [
            ('annee_courante_id', '=', annee_id),
            ('state', '=', 'actif'),
        ]
        
        students = self.env['ensiasd.student'].search(domain)
        bulletins = self.env['ensiasd.bulletin']
        
        for student in students:
            filiere = student.groupe_id.filiere_id if hasattr(student.groupe_id, 'filiere_id') else False
            if filiere_id and filiere and filiere.id != filiere_id:
                continue
            
            existing = self.search([
                ('student_id', '=', student.id),
                ('annee_id', '=', annee_id),
                ('type_bulletin', '=', type_bulletin),
            ], limit=1)
            
            if not existing:
                bulletin = self.create({
                    'student_id': student.id,
                    'annee_id': annee_id,
                    'type_bulletin': type_bulletin,
                    'filiere_id': filiere.id if filiere else filiere_id,
                })
                bulletins |= bulletin
            else:
                bulletins |= existing
        
        bulletins.action_generate()
        return bulletins


class EnsiasdBulletinLine(models.Model):
    """
    Ligne de bulletin (note par module)
    """
    _name = 'ensiasd.bulletin.line'
    _description = 'Ligne de bulletin'
    _order = 'module_id'

    bulletin_id = fields.Many2one(
        'ensiasd.bulletin',
        string='Bulletin',
        required=True,
        ondelete='cascade'
    )
    
    note_id = fields.Many2one(
        'ensiasd.note',
        string='Note'
    )
    
    module_id = fields.Many2one(
        'ensiasd.module',
        string='Module',
        required=True
    )
    
    module_code = fields.Char(related='module_id.code', string='Code')
    module_name = fields.Char(related='module_id.name', string='Intitulé')
    
    note_cc = fields.Float(string='CC', digits=(4, 2))
    note_tp = fields.Float(string='TP', digits=(4, 2))
    note_examen = fields.Float(string='Examen', digits=(4, 2))
    note_rattrapage = fields.Float(string='Ratt.', digits=(4, 2))
    note_finale = fields.Float(string='Finale', digits=(4, 2))
    
    credits = fields.Integer(string='Crédits')
    coefficient = fields.Float(string='Coef.')
    
    resultat = fields.Selection([
        ('en_cours', 'En cours'),
        ('valide', 'V'),
        ('non_valide', 'NV'),
        ('rattrapage', 'R'),
        ('elimine', 'E'),
        ('compense', 'C'),
        ('absent', 'ABS'),
    ], string='Rés.')
