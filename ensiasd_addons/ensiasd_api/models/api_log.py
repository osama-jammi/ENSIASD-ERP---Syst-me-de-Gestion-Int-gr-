# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EnsiasdApiLog(models.Model):
    """Logs des requêtes API"""
    _name = 'ensiasd.api.log'
    _description = 'Log API ENSIASD'
    _order = 'timestamp desc'

    timestamp = fields.Datetime(
        string='Date/Heure',
        default=fields.Datetime.now,
        readonly=True
    )
    
    endpoint = fields.Char(string='Endpoint', readonly=True)
    method = fields.Selection([
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    ], string='Méthode', readonly=True)
    
    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        readonly=True
    )
    
    ip_address = fields.Char(string='IP', readonly=True)
    user_agent = fields.Char(string='User Agent', readonly=True)
    
    request_data = fields.Text(string='Requête', readonly=True)
    response_code = fields.Integer(string='Code réponse', readonly=True)
    response_time_ms = fields.Integer(string='Temps (ms)', readonly=True)
    
    status = fields.Selection([
        ('success', 'Succès'),
        ('error', 'Erreur'),
        ('auth_failed', 'Auth échouée'),
        ('rate_limited', 'Rate limited'),
    ], string='Statut', readonly=True)
    
    error_message = fields.Text(string='Message erreur', readonly=True)

    @api.model
    def log_request(self, endpoint, method, student_id=None, ip_address=None,
                    user_agent=None, request_data=None, response_code=200,
                    response_time_ms=0, status='success', error_message=None):
        """Enregistre une requête API"""
        config = self.env['ensiasd.api.config'].get_config()
        
        if not config.enable_logging:
            return False
        
        # Incrémenter le compteur total
        config.sudo().write({
            'total_requests': config.total_requests + 1
        })
        
        return self.create({
            'endpoint': endpoint,
            'method': method,
            'student_id': student_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'request_data': str(request_data) if request_data else None,
            'response_code': response_code,
            'response_time_ms': response_time_ms,
            'status': status,
            'error_message': error_message,
        })
