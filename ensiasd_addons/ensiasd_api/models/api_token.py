# -*- coding: utf-8 -*-
import secrets
import hashlib
from datetime import datetime, timedelta
from odoo import models, fields, api


class EnsiasdApiToken(models.Model):
    """Tokens d'authentification pour les étudiants"""
    _name = 'ensiasd.api.token'
    _description = 'Token API Étudiant'
    _order = 'create_date desc'

    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        required=True,
        ondelete='cascade'
    )
    
    token = fields.Char(string='Token', readonly=True, index=True)
    token_hash = fields.Char(string='Hash Token', readonly=True, index=True)
    
    expires_at = fields.Datetime(string='Expire le', readonly=True)
    last_used = fields.Datetime(string='Dernière utilisation')
    
    ip_address = fields.Char(string='Adresse IP')
    user_agent = fields.Char(string='User Agent')
    
    is_valid = fields.Boolean(
        string='Valide',
        compute='_compute_is_valid',
        store=True
    )
    
    revoked = fields.Boolean(string='Révoqué', default=False)
    revoked_at = fields.Datetime(string='Révoqué le')

    @api.depends('expires_at', 'revoked')
    def _compute_is_valid(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_valid = (
                not record.revoked and 
                record.expires_at and 
                record.expires_at > now
            )

    @api.model
    def create_token(self, student_id, ip_address=None, user_agent=None):
        """Crée un nouveau token pour un étudiant"""
        config = self.env['ensiasd.api.config'].get_config()
        
        # Générer le token
        raw_token = secrets.token_hex(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Calculer l'expiration
        expires_at = datetime.now() + timedelta(hours=config.token_expiry_hours)
        
        # Révoquer les anciens tokens de cet étudiant
        self.search([
            ('student_id', '=', student_id),
            ('revoked', '=', False)
        ]).write({
            'revoked': True,
            'revoked_at': fields.Datetime.now()
        })
        
        # Créer le nouveau token
        token = self.create({
            'student_id': student_id,
            'token': raw_token,
            'token_hash': token_hash,
            'expires_at': expires_at,
            'ip_address': ip_address,
            'user_agent': user_agent,
        })
        
        return {
            'token': raw_token,
            'expires_at': expires_at.isoformat(),
            'student_id': student_id,
        }

    @api.model
    def validate_token(self, token):
        """Valide un token et retourne l'étudiant associé"""
        if not token:
            return False
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        token_record = self.search([
            ('token_hash', '=', token_hash),
            ('revoked', '=', False),
        ], limit=1)
        
        if not token_record or not token_record.is_valid:
            return False
        
        # Mettre à jour la dernière utilisation
        token_record.write({'last_used': fields.Datetime.now()})
        
        return token_record.student_id

    def action_revoke(self):
        """Révoque le token"""
        self.write({
            'revoked': True,
            'revoked_at': fields.Datetime.now()
        })
