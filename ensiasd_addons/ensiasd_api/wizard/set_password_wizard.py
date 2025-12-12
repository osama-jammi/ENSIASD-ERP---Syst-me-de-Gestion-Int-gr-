# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SetApiPasswordWizard(models.TransientModel):
    """Wizard pour définir le mot de passe API d'un étudiant"""
    _name = 'set.api.password.wizard'
    _description = 'Définir mot de passe API'

    student_id = fields.Many2one('ensiasd.student', string='Étudiant', required=True)
    password = fields.Char(string='Nouveau mot de passe', required=True)
    confirm_password = fields.Char(string='Confirmer le mot de passe', required=True)

    @api.constrains('password', 'confirm_password')
    def _check_passwords(self):
        for record in self:
            if record.password != record.confirm_password:
                raise ValidationError("Les mots de passe ne correspondent pas!")
            if len(record.password) < 6:
                raise ValidationError("Le mot de passe doit contenir au moins 6 caractères!")

    def action_set_password(self):
        """Définit le mot de passe API"""
        self.ensure_one()
        self.student_id.set_api_password(self.password)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Succès',
                'message': f'Mot de passe API défini pour {self.student_id.name}',
                'type': 'success',
                'sticky': False,
            }
        }
