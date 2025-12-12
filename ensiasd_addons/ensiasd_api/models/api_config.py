# -*- coding: utf-8 -*-
import secrets
from odoo import models, fields, api


class EnsiasdApiConfig(models.Model):
    """Configuration de l'API ENSIASD"""
    _name = 'ensiasd.api.config'
    _description = 'Configuration API ENSIASD'
    _rec_name = 'name'

    name = fields.Char(string='Nom', default='Configuration API', required=True)
    
    # Clé API principale (pour authentifier l'application Django)
    api_key = fields.Char(string='Clé API', readonly=True)
    api_secret = fields.Char(string='Secret API', readonly=True)
    
    # Paramètres
    token_expiry_hours = fields.Integer(
        string='Expiration token (heures)',
        default=24,
        help="Durée de validité des tokens d'authentification"
    )
    max_requests_per_minute = fields.Integer(
        string='Requêtes max/minute',
        default=60,
        help="Limite de requêtes par minute par utilisateur"
    )
    
    # Fonctionnalités activées
    enable_notes = fields.Boolean(string='API Notes', default=True)
    enable_absences = fields.Boolean(string='API Absences', default=True)
    enable_emploi_temps = fields.Boolean(string='API Emploi du temps', default=True)
    enable_stages = fields.Boolean(string='API Stages', default=True)
    
    # Logs
    enable_logging = fields.Boolean(string='Activer les logs', default=True)
    log_retention_days = fields.Integer(string='Rétention logs (jours)', default=30)
    
    # Statistiques
    total_requests = fields.Integer(string='Total requêtes', readonly=True, default=0)
    active_tokens = fields.Integer(string='Tokens actifs', compute='_compute_active_tokens')
    
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Génère automatiquement les clés API à la création"""
        for vals in vals_list:
            if not vals.get('api_key'):
                vals['api_key'] = f"ensiasd_{secrets.token_hex(16)}"
            if not vals.get('api_secret'):
                vals['api_secret'] = secrets.token_hex(32)
        return super().create(vals_list)

    @api.model
    def get_config(self):
        """Récupère ou crée la configuration API"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            config = self.create({
                'name': 'Configuration API ENSIASD',
            })
        # Si les clés sont vides, les générer
        if not config.api_key:
            config.action_generate_keys()
        return config

    def action_generate_keys(self):
        """Génère de nouvelles clés API"""
        self.write({
            'api_key': f"ensiasd_{secrets.token_hex(16)}",
            'api_secret': secrets.token_hex(32),
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Clés générées',
                'message': f'Nouvelle clé API: {self.api_key}',
                'type': 'success',
                'sticky': True,
            }
        }

    def _compute_active_tokens(self):
        """Compte les tokens actifs"""
        for record in self:
            record.active_tokens = self.env['ensiasd.api.token'].search_count([
                ('is_valid', '=', True)
            ])

    def action_view_logs(self):
        """Action pour voir les logs"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Logs API',
            'res_model': 'ensiasd.api.log',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def action_cleanup_logs(self):
        """Nettoie les anciens logs"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=self.log_retention_days)
        old_logs = self.env['ensiasd.api.log'].search([
            ('timestamp', '<', cutoff_date)
        ])
        old_logs.unlink()
        return True
