# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class EnsiasdAppelWizard(models.TransientModel):
    """
    Wizard pour faire l'appel d'une séance
    """
    _name = 'ensiasd.appel.wizard'
    _description = 'Assistant d\'appel'

    seance_id = fields.Many2one(
        'ensiasd.seance',
        string='Séance',
        required=True
    )
    
    date = fields.Date(
        related='seance_id.date',
        string='Date'
    )
    
    module_name = fields.Char(
        related='seance_id.element_id.module_id.name',
        string='Module'
    )
    
    line_ids = fields.One2many(
        'ensiasd.appel.wizard.line',
        'wizard_id',
        string='Étudiants'
    )
    
    total_etudiants = fields.Integer(
        string='Total',
        compute='_compute_stats'
    )
    
    presents = fields.Integer(
        string='Présents',
        compute='_compute_stats'
    )
    
    absents = fields.Integer(
        string='Absents',
        compute='_compute_stats'
    )

    @api.depends('line_ids', 'line_ids.is_absent')
    def _compute_stats(self):
        for record in self:
            record.total_etudiants = len(record.line_ids)
            record.absents = len(record.line_ids.filtered('is_absent'))
            record.presents = record.total_etudiants - record.absents

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        seance_id = self._context.get('default_seance_id')
        if seance_id:
            seance = self.env['ensiasd.seance'].browse(seance_id)
            
            # Récupérer les étudiants des groupes de la séance
            students = self.env['ensiasd.student']
            for groupe in seance.groupe_ids:
                students |= groupe.student_ids.filtered(lambda s: s.state == 'actif')
            
            # Récupérer les absences existantes
            existing_absences = self.env['ensiasd.absence'].search([
                ('seance_id', '=', seance_id)
            ])
            absent_student_ids = existing_absences.mapped('student_id.id')
            
            lines = []
            for student in students.sorted(key=lambda s: s.name):
                lines.append((0, 0, {
                    'student_id': student.id,
                    'is_absent': student.id in absent_student_ids,
                }))
            
            res['line_ids'] = lines
        
        return res

    def action_save_appel(self):
        """Enregistrer l'appel"""
        self.ensure_one()
        
        Absence = self.env['ensiasd.absence']
        
        # Supprimer les absences existantes pour cette séance
        existing = Absence.search([('seance_id', '=', self.seance_id.id)])
        existing.unlink()
        
        # Créer les nouvelles absences
        for line in self.line_ids.filtered('is_absent'):
            Absence.create({
                'student_id': line.student_id.id,
                'seance_id': self.seance_id.id,
                'state': 'absent',
            })
        
        # Marquer la séance comme appel fait
        self.seance_id.write({
            'appel_fait': True,
            'date_appel': fields.Datetime.now(),
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Appel enregistré',
                'message': f'{self.absents} absence(s) enregistrée(s) sur {self.total_etudiants} étudiants.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_mark_all_present(self):
        """Marquer tous comme présents"""
        self.line_ids.write({'is_absent': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_mark_all_absent(self):
        """Marquer tous comme absents"""
        self.line_ids.write({'is_absent': True})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class EnsiasdAppelWizardLine(models.TransientModel):
    """
    Ligne du wizard d'appel
    """
    _name = 'ensiasd.appel.wizard.line'
    _description = 'Ligne d\'appel'
    _order = 'student_name'

    wizard_id = fields.Many2one(
        'ensiasd.appel.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        required=True
    )
    
    student_name = fields.Char(
        related='student_id.name',
        string='Nom'
    )
    
    student_cne = fields.Char(
        related='student_id.cne',
        string='CNE'
    )
    
    is_absent = fields.Boolean(
        string='Absent',
        default=False
    )


class EnsiasdSendAppelWizard(models.TransientModel):
    """
    Wizard pour envoyer le formulaire d'appel par email
    """
    _name = 'ensiasd.send.appel.wizard'
    _description = 'Envoyer formulaire d\'appel'

    seance_ids = fields.Many2many(
        'ensiasd.seance',
        string='Séances',
        required=True
    )
    
    send_to = fields.Selection([
        ('enseignant', 'Enseignant de la séance'),
        ('all_teachers', 'Tous les enseignants'),
        ('custom', 'Email personnalisé'),
    ], string='Envoyer à', default='enseignant', required=True)
    
    custom_email = fields.Char(string='Email')
    
    include_student_list = fields.Boolean(
        string='Inclure la liste des étudiants',
        default=True
    )
    
    validity_hours = fields.Integer(
        string='Validité du lien (heures)',
        default=48
    )

    def action_send(self):
        """Envoyer les formulaires"""
        self.ensure_one()
        
        Token = self.env['ensiasd.absence.token']
        
        for seance in self.seance_ids:
            # Créer le token
            token = Token.create_token(
                seance.id,
                seance.enseignant_id.id if seance.enseignant_id else None,
                self.validity_hours
            )
            
            # Envoyer l'email
            template = self.env.ref('ensiasd_absence.mail_template_appel_seance', raise_if_not_found=False)
            if template:
                # Déterminer le destinataire
                if self.send_to == 'enseignant' and seance.enseignant_id:
                    email = seance.enseignant_id.work_email
                elif self.send_to == 'custom':
                    email = self.custom_email
                else:
                    continue
                
                if email:
                    template.with_context(
                        token=token.token,
                        recipient_email=email,
                    ).send_mail(seance.id, force_send=True)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Formulaires envoyés',
                'message': f'{len(self.seance_ids)} formulaire(s) d\'appel envoyé(s).',
                'type': 'success',
                'sticky': False,
            }
        }
