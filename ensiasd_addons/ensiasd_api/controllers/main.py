# -*- coding: utf-8 -*-
import json
import time
import logging
from functools import wraps

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


def json_response(data, status=200):
    """Helper pour créer une réponse JSON"""
    return Response(
        json.dumps(data, ensure_ascii=False, default=str),
        status=status,
        content_type='application/json; charset=utf-8'
    )


def api_error(message, status=400, code=None):
    """Helper pour créer une réponse d'erreur"""
    return json_response({
        'success': False,
        'error': {
            'message': message,
            'code': code or f'ERR_{status}'
        }
    }, status=status)


def require_api_key(func):
    """Décorateur pour vérifier la clé API"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.httprequest.headers.get('X-API-Key')
        
        if not api_key:
            return api_error('Clé API manquante', 401, 'MISSING_API_KEY')
        
        config = request.env['ensiasd.api.config'].sudo().get_config()
        
        if api_key != config.api_key:
            return api_error('Clé API invalide', 401, 'INVALID_API_KEY')
        
        return func(*args, **kwargs)
    return wrapper


def require_token(func):
    """Décorateur pour vérifier le token étudiant"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.httprequest.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return api_error('Token manquant', 401, 'MISSING_TOKEN')
        
        token = auth_header[7:]  # Enlever 'Bearer '
        
        student = request.env['ensiasd.api.token'].sudo().validate_token(token)
        
        if not student:
            return api_error('Token invalide ou expiré', 401, 'INVALID_TOKEN')
        
        # Ajouter l'étudiant au contexte
        request.student = student
        
        return func(*args, **kwargs)
    return wrapper


def log_request(endpoint, method='GET'):
    """Décorateur pour logger les requêtes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            student_id = getattr(request, 'student', None)
            student_id = student_id.id if student_id else None
            
            try:
                result = func(*args, **kwargs)
                response_time = int((time.time() - start_time) * 1000)
                
                # Logger la requête
                request.env['ensiasd.api.log'].sudo().log_request(
                    endpoint=endpoint,
                    method=method,
                    student_id=student_id,
                    ip_address=request.httprequest.remote_addr,
                    user_agent=request.httprequest.user_agent.string[:200] if request.httprequest.user_agent else None,
                    response_code=getattr(result, 'status_code', 200) if hasattr(result, 'status_code') else 200,
                    response_time_ms=response_time,
                    status='success'
                )
                
                return result
                
            except Exception as e:
                response_time = int((time.time() - start_time) * 1000)
                
                request.env['ensiasd.api.log'].sudo().log_request(
                    endpoint=endpoint,
                    method=method,
                    student_id=student_id,
                    ip_address=request.httprequest.remote_addr,
                    response_code=500,
                    response_time_ms=response_time,
                    status='error',
                    error_message=str(e)
                )
                
                _logger.exception(f"API Error: {endpoint}")
                return api_error('Erreur interne du serveur', 500, 'INTERNAL_ERROR')
        
        return wrapper
    return decorator


class EnsiasdApiController(http.Controller):
    """Controller principal de l'API ENSIASD"""

    # ========== ENDPOINTS PUBLICS ==========

    @http.route('/api/v1/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health_check(self):
        """Vérification de santé de l'API"""
        return json_response({
            'status': 'ok',
            'service': 'ENSIASD API',
            'version': '1.0.0'
        })

    @http.route('/api/v1/info', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    def api_info(self):
        """Informations sur l'API"""
        config = request.env['ensiasd.api.config'].sudo().get_config()
        return json_response({
            'success': True,
            'data': {
                'name': 'ENSIASD Student API',
                'version': '1.0.0',
                'features': {
                    'notes': config.enable_notes,
                    'absences': config.enable_absences,
                    'emploi_temps': config.enable_emploi_temps,
                    'stages': config.enable_stages,
                }
            }
        })

    # ========== AUTHENTIFICATION ==========

    @http.route('/api/v1/auth/login', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_key
    @log_request('/auth/login', 'POST')
    def login(self):
        """Authentification d'un étudiant"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return api_error('JSON invalide', 400, 'INVALID_JSON')
        
        cne = data.get('cne')
        password = data.get('password')
        
        if not cne or not password:
            return api_error('CNE et mot de passe requis', 400, 'MISSING_CREDENTIALS')
        
        student = request.env['ensiasd.student'].sudo().authenticate_api(cne, password)
        
        if not student:
            request.env['ensiasd.api.log'].sudo().log_request(
                endpoint='/auth/login',
                method='POST',
                ip_address=request.httprequest.remote_addr,
                status='auth_failed',
                error_message=f'Échec auth pour CNE: {cne}'
            )
            return api_error('Identifiants invalides', 401, 'AUTH_FAILED')
        
        # Créer le token
        token_data = request.env['ensiasd.api.token'].sudo().create_token(
            student_id=student.id,
            ip_address=request.httprequest.remote_addr,
            user_agent=request.httprequest.user_agent.string[:200] if request.httprequest.user_agent else None
        )
        
        return json_response({
            'success': True,
            'data': {
                'token': token_data['token'],
                'expires_at': token_data['expires_at'],
                'student': student.to_api_dict()
            }
        })

    @http.route('/api/v1/auth/logout', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/auth/logout', 'POST')
    def logout(self):
        """Déconnexion - révoque le token"""
        auth_header = request.httprequest.headers.get('Authorization')
        token = auth_header[7:] if auth_header else None
        
        if token:
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            token_record = request.env['ensiasd.api.token'].sudo().search([
                ('token_hash', '=', token_hash)
            ], limit=1)
            if token_record:
                token_record.action_revoke()
        
        return json_response({
            'success': True,
            'message': 'Déconnexion réussie'
        })

    @http.route('/api/v1/auth/refresh', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/auth/refresh', 'POST')
    def refresh_token(self):
        """Rafraîchit le token"""
        student = request.student
        
        token_data = request.env['ensiasd.api.token'].sudo().create_token(
            student_id=student.id,
            ip_address=request.httprequest.remote_addr,
            user_agent=request.httprequest.user_agent.string[:200] if request.httprequest.user_agent else None
        )
        
        return json_response({
            'success': True,
            'data': {
                'token': token_data['token'],
                'expires_at': token_data['expires_at']
            }
        })

    # ========== PROFIL ÉTUDIANT ==========

    @http.route('/api/v1/me', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/me', 'GET')
    def get_profile(self):
        """Récupère le profil de l'étudiant connecté"""
        student = request.student
        return json_response({
            'success': True,
            'data': student.sudo().to_api_dict(include_details=True)
        })

    @http.route('/api/v1/me/password', type='http', auth='none', methods=['PUT'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/me/password', 'PUT')
    def change_password(self):
        """Change le mot de passe API de l'étudiant"""
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return api_error('JSON invalide', 400, 'INVALID_JSON')
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return api_error('Ancien et nouveau mot de passe requis', 400)
        
        if len(new_password) < 8:
            return api_error('Le mot de passe doit faire au moins 8 caractères', 400)
        
        student = request.student.sudo()
        
        if not student.check_api_password(old_password):
            return api_error('Ancien mot de passe incorrect', 400)
        
        student.set_api_password(new_password)
        
        return json_response({
            'success': True,
            'message': 'Mot de passe modifié avec succès'
        })

    # ========== NOTES ==========

    @http.route('/api/v1/notes', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/notes', 'GET')
    def get_notes(self):
        """Récupère les notes de l'étudiant"""
        config = request.env['ensiasd.api.config'].sudo().get_config()
        if not config.enable_notes:
            return api_error('API Notes désactivée', 403, 'FEATURE_DISABLED')
        
        student = request.student.sudo()
        
        # Paramètres optionnels
        annee_id = request.params.get('annee_id')
        module_id = request.params.get('module_id')
        
        if annee_id:
            annee_id = int(annee_id)
        if module_id:
            module_id = int(module_id)
        
        notes = student.get_notes_api(annee_id=annee_id, module_id=module_id)
        
        return json_response({
            'success': True,
            'data': notes,
            'count': len(notes)
        })

    @http.route('/api/v1/notes/summary', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/notes/summary', 'GET')
    def get_notes_summary(self):
        """Récupère un résumé des notes (moyennes par module)"""
        config = request.env['ensiasd.api.config'].sudo().get_config()
        if not config.enable_notes:
            return api_error('API Notes désactivée', 403, 'FEATURE_DISABLED')
        
        student = request.student.sudo()
        annee_id = request.params.get('annee_id')
        
        notes = student.get_notes_api(annee_id=int(annee_id) if annee_id else None)
        
        # Calculer les moyennes par module
        modules = {}
        for note in notes:
            if note['module']:
                mod_id = note['module']['id']
                if mod_id not in modules:
                    modules[mod_id] = {
                        'module': note['module'],
                        'notes': [],
                        'total_coef': 0,
                        'total_weighted': 0
                    }
                modules[mod_id]['notes'].append(note)
                modules[mod_id]['total_coef'] += note['coefficient']
                modules[mod_id]['total_weighted'] += note['valeur'] * note['coefficient']
        
        summary = []
        for mod_id, data in modules.items():
            moyenne = data['total_weighted'] / data['total_coef'] if data['total_coef'] > 0 else 0
            summary.append({
                'module': data['module'],
                'moyenne': round(moyenne, 2),
                'nb_notes': len(data['notes']),
                'notes': data['notes']
            })
        
        return json_response({
            'success': True,
            'data': summary
        })

    # ========== ABSENCES ==========

    @http.route('/api/v1/absences', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/absences', 'GET')
    def get_absences(self):
        """Récupère les absences de l'étudiant"""
        config = request.env['ensiasd.api.config'].sudo().get_config()
        if not config.enable_absences:
            return api_error('API Absences désactivée', 403, 'FEATURE_DISABLED')
        
        student = request.student.sudo()
        
        # Paramètres optionnels
        annee_id = request.params.get('annee_id')
        date_from = request.params.get('date_from')
        date_to = request.params.get('date_to')
        
        if annee_id:
            annee_id = int(annee_id)
        
        absences = student.get_absences_api(
            annee_id=annee_id,
            date_from=date_from,
            date_to=date_to
        )
        
        return json_response({
            'success': True,
            'data': absences,
            'count': len(absences)
        })

    @http.route('/api/v1/absences/summary', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/absences/summary', 'GET')
    def get_absences_summary(self):
        """Récupère un résumé des absences"""
        config = request.env['ensiasd.api.config'].sudo().get_config()
        if not config.enable_absences:
            return api_error('API Absences désactivée', 403, 'FEATURE_DISABLED')
        
        student = request.student.sudo()
        absences = student.get_absences_api()
        
        total = len(absences)
        justifiees = sum(1 for a in absences if a.get('justifiee'))
        non_justifiees = total - justifiees
        
        return json_response({
            'success': True,
            'data': {
                'total': total,
                'justifiees': justifiees,
                'non_justifiees': non_justifiees
            }
        })

    # ========== EMPLOI DU TEMPS ==========

    @http.route('/api/v1/emploi-temps', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/emploi-temps', 'GET')
    def get_emploi_temps(self):
        """Récupère l'emploi du temps de l'étudiant"""
        config = request.env['ensiasd.api.config'].sudo().get_config()
        if not config.enable_emploi_temps:
            return api_error('API Emploi du temps désactivée', 403, 'FEATURE_DISABLED')
        
        student = request.student.sudo()
        
        # Paramètres optionnels
        date_from = request.params.get('date_from')
        date_to = request.params.get('date_to')
        
        seances = student.get_emploi_temps_api(date_from=date_from, date_to=date_to)
        
        return json_response({
            'success': True,
            'data': seances,
            'count': len(seances)
        })

    # ========== INSCRIPTIONS ==========

    @http.route('/api/v1/inscriptions', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/inscriptions', 'GET')
    def get_inscriptions(self):
        """Récupère les inscriptions aux modules"""
        student = request.student.sudo()
        
        annee_id = request.params.get('annee_id')
        if annee_id:
            annee_id = int(annee_id)
        
        inscriptions = student.get_inscriptions_api(annee_id=annee_id)
        
        return json_response({
            'success': True,
            'data': inscriptions,
            'count': len(inscriptions)
        })

    # ========== STAGES ==========

    @http.route('/api/v1/stages', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/stages', 'GET')
    def get_stages(self):
        """Récupère les stages de l'étudiant"""
        config = request.env['ensiasd.api.config'].sudo().get_config()
        if not config.enable_stages:
            return api_error('API Stages désactivée', 403, 'FEATURE_DISABLED')
        
        student = request.student.sudo()
        stages = student.get_stages_api()
        
        return json_response({
            'success': True,
            'data': stages,
            'count': len(stages)
        })

    # ========== DONNÉES DE RÉFÉRENCE ==========

    @http.route('/api/v1/annees', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/annees', 'GET')
    def get_annees(self):
        """Liste des années universitaires"""
        annees = request.env['ensiasd.annee'].sudo().search([])
        
        data = [{
            'id': a.id,
            'name': a.name,
            'is_current': a.is_current,
            'date_debut': a.date_debut.isoformat() if hasattr(a, 'date_debut') and a.date_debut else None,
            'date_fin': a.date_fin.isoformat() if hasattr(a, 'date_fin') and a.date_fin else None,
        } for a in annees]
        
        return json_response({
            'success': True,
            'data': data
        })

    @http.route('/api/v1/modules', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/modules', 'GET')
    def get_modules(self):
        """Liste des modules disponibles"""
        student = request.student.sudo()
        
        # Récupérer les modules via les inscriptions
        inscriptions = student.get_inscriptions_api()
        modules = [insc['module'] for insc in inscriptions if insc['module']]
        
        return json_response({
            'success': True,
            'data': modules
        })
