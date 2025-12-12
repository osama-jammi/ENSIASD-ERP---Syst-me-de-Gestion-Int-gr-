# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class DeliberationWizard(models.TransientModel):
    """
    Assistant de création de délibération
    """
    _name = 'ensiasd.deliberation.wizard'
    _description = 'Assistant de délibération'

    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True,
        default=lambda self: self._default_annee()
    )
    
    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session',
        required=True,
        domain="[('annee_id', '=', annee_id), ('state', '=', 'closed')]"
    )
    
    filiere_id = fields.Many2one(
        'ensiasd.filiere',
        string='Filière',
        required=True
    )
    
    type_deliberation = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
        ('annee', 'Fin d\'année'),
    ], string='Type', required=True)
    
    date = fields.Datetime(
        string='Date de délibération',
        required=True,
        default=fields.Datetime.now
    )
    
    lieu = fields.Char(string='Lieu')
    
    president_id = fields.Many2one(
        'hr.employee',
        string='Président du jury',
        domain=[('is_enseignant', '=', True)]
    )
    
    membre_ids = fields.Many2many(
        'hr.employee',
        'deliberation_wizard_membre_rel',
        'wizard_id',
        'employee_id',
        string='Membres du jury',
        domain=[('is_enseignant', '=', True)]
    )
    
    # Statistiques prévisionnelles
    nb_etudiants = fields.Integer(
        string='Étudiants concernés',
        compute='_compute_preview',
        readonly=True
    )
    
    nb_notes_manquantes = fields.Integer(
        string='Notes manquantes',
        compute='_compute_preview',
        readonly=True
    )

    def _default_annee(self):
        config = self.env['ensiasd.config'].get_config()
        return config.annee_courante_id

    @api.depends('annee_id', 'filiere_id', 'type_deliberation')
    def _compute_preview(self):
        for record in self:
            if not all([record.annee_id, record.filiere_id, record.type_deliberation]):
                record.nb_etudiants = 0
                record.nb_notes_manquantes = 0
                continue
            
            # Compter les inscriptions
            domain = [
                ('annee_id', '=', record.annee_id.id),
                ('module_id.filiere_id', '=', record.filiere_id.id),
                ('state', '=', 'validated'),
            ]
            
            if record.type_deliberation != 'annee':
                domain.append(('module_id.semestre', '=', record.type_deliberation))
            
            inscriptions = self.env['ensiasd.inscription'].search(domain)
            students = inscriptions.mapped('student_id')
            record.nb_etudiants = len(students)
            
            # Compter les notes manquantes
            missing = 0
            for inscription in inscriptions:
                notes = self.env['ensiasd.note'].search([
                    ('inscription_id', '=', inscription.id),
                    ('state', 'in', ['validated', 'locked']),
                ])
                if not notes:
                    missing += 1
            
            record.nb_notes_manquantes = missing

    def action_create_deliberation(self):
        """Créer la délibération"""
        self.ensure_one()
        
        # Vérifications
        if self.nb_notes_manquantes > 0:
            raise UserError(
                f"Il manque {self.nb_notes_manquantes} notes. "
                "Veuillez compléter la saisie avant de créer la délibération."
            )
        
        # Créer la délibération
        deliberation = self.env['ensiasd.deliberation'].create({
            'annee_id': self.annee_id.id,
            'session_id': self.session_id.id,
            'filiere_id': self.filiere_id.id,
            'type_deliberation': self.type_deliberation,
            'date': self.date,
            'lieu': self.lieu,
            'president_id': self.president_id.id if self.president_id else False,
            'membre_ids': [(6, 0, self.membre_ids.ids)],
        })
        
        # Ouvrir la délibération créée
        return {
            'type': 'ir.actions.act_window',
            'name': 'Délibération',
            'res_model': 'ensiasd.deliberation',
            'res_id': deliberation.id,
            'view_mode': 'form',
            'target': 'current',
        }


class BulletinWizard(models.TransientModel):
    """
    Assistant de génération de bulletins
    """
    _name = 'ensiasd.bulletin.wizard'
    _description = 'Assistant de génération de bulletins'

    mode = fields.Selection([
        ('single', 'Un seul étudiant'),
        ('batch', 'Génération en lot'),
    ], string='Mode', default='single', required=True)
    
    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant'
    )
    
    annee_id = fields.Many2one(
        'ensiasd.annee',
        string='Année académique',
        required=True,
        default=lambda self: self._default_annee()
    )
    
    filiere_id = fields.Many2one(
        'ensiasd.filiere',
        string='Filière'
    )
    
    type_bulletin = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
        ('S3', 'Semestre 3'),
        ('S4', 'Semestre 4'),
        ('S5', 'Semestre 5'),
        ('S6', 'Semestre 6'),
        ('annuel', 'Annuel'),
    ], string='Type', required=True)
    
    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session',
        domain="[('annee_id', '=', annee_id)]"
    )

    def _default_annee(self):
        config = self.env['ensiasd.config'].get_config()
        return config.annee_courante_id

    def action_generate(self):
        """Générer le(s) bulletin(s)"""
        self.ensure_one()
        
        if self.mode == 'single':
            if not self.student_id:
                raise UserError("Veuillez sélectionner un étudiant!")
            
            # Créer un bulletin
            bulletin = self.env['ensiasd.bulletin'].create({
                'student_id': self.student_id.id,
                'annee_id': self.annee_id.id,
                'type_bulletin': self.type_bulletin,
                'filiere_id': self.filiere_id.id if self.filiere_id else 
                             (self.student_id.groupe_id.filiere_id.id if hasattr(self.student_id.groupe_id, 'filiere_id') else False),
                'session_id': self.session_id.id if self.session_id else False,
            })
            
            bulletin.action_generate()
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bulletin',
                'res_model': 'ensiasd.bulletin',
                'res_id': bulletin.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        else:
            # Génération en lot
            if not self.filiere_id:
                raise UserError("Veuillez sélectionner une filière pour la génération en lot!")
            
            bulletins = self.env['ensiasd.bulletin'].generate_bulletins_batch(
                self.annee_id.id,
                self.type_bulletin,
                self.filiere_id.id
            )
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bulletins générés',
                'res_model': 'ensiasd.bulletin',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', bulletins.ids)],
                'target': 'current',
            }
