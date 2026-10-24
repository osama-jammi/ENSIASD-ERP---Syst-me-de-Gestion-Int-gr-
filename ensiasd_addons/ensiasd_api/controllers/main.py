# -*- coding: utf-8 -*-
"""
Controller HTTP REST principal de l'API ENSIASD.

Routes disponibles (préfixe /api/v1) :
  Public :
    GET  /health
    GET  /info

  Authentification :
    POST /auth/login
    POST /auth/logout
    POST /auth/refresh

  Profil étudiant :
    GET  /me
    PUT  /me/password

  Notes :
    GET  /notes
    GET  /notes/summary

  Absences :
    GET  /absences
    GET  /absences/summary

  Emploi du temps :
    GET  /emploi-temps

  Inscriptions / modules :
    GET  /inscriptions
    GET  /modules

  Stages (nécessite ensiasd_stage) :
    GET  /stages

  Années :
    GET  /annees

  Réclamations (nécessite ensiasd_reclamation) :
    GET  /reclamations
    POST /reclamations
    GET  /reclamations/<int:reclamation_id>
"""

import json
import time
import logging
from functools import wraps

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers réponses JSON
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Décorateurs d'authentification
# ---------------------------------------------------------------------------

def require_api_key(func):
    """Décorateur pour vérifier la clé API (header X-API-Key)"""
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
    """Décorateur pour vérifier le token Bearer de l'étudiant"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.httprequest.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return api_error('Token manquant', 401, 'MISSING_TOKEN')

        token = auth_header[7:]  # Enlever 'Bearer '

        student = request.env['ensiasd.api.token'].sudo().validate_token(token)

        if not student:
            return api_error('Token invalide ou expiré', 401, 'INVALID_TOKEN')

        # Attacher l'étudiant au contexte de la requête
        request.student = student

        return func(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Décorateur de logging
# ---------------------------------------------------------------------------

def log_request(endpoint, method='GET'):
    """Décorateur pour logger les requêtes API dans ensiasd.api.log"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            student_obj = getattr(request, 'student', None)
            student_id = student_obj.id if student_obj else None

            try:
                result = func(*args, **kwargs)
                response_time = int((time.time() - start_time) * 1000)

                # Déterminer le code HTTP retourné
                response_code = 200
                if hasattr(result, 'status_code'):
                    response_code = result.status_code

                request.env['ensiasd.api.log'].sudo().log_request(
                    endpoint=endpoint,
                    method=method,
                    student_id=student_id,
                    ip_address=request.httprequest.remote_addr,
                    user_agent=(
                        request.httprequest.user_agent.string[:200]
                        if request.httprequest.user_agent else None
                    ),
                    response_code=response_code,
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


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _check_feature(feature_name):
    """
    Vérifie si une fonctionnalité API est activée dans la configuration.
    Retourne None si activée, ou une réponse d'erreur 403 sinon.
    """
    config = request.env['ensiasd.api.config'].sudo().get_config()
    enabled = getattr(config, f'enable_{feature_name}', True)
    if not enabled:
        label = feature_name.replace('_', ' ').capitalize()
        return api_error(f'API {label} désactivée', 403, 'FEATURE_DISABLED')
    return None


def _model_available(model_name):
    """
    Vérifie si un modèle Odoo est disponible (module installé).
    Retourne None si disponible, ou une réponse d'erreur 503 sinon.
    """
    if model_name not in request.env:
        return api_error(
            f"Module non installé (modèle '{model_name}' introuvable). "
            f"Installez le module Odoo correspondant.",
            503, 'MODULE_NOT_INSTALLED'
        )
    return None


def _parse_json_body():
    """
    Parse le corps JSON de la requête.
    Retourne (data, None) si succès, ou (None, réponse_erreur) si JSON invalide.
    """
    try:
        data = json.loads(request.httprequest.data.decode('utf-8'))
        return data, None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, api_error('Corps JSON invalide', 400, 'INVALID_JSON')


# ---------------------------------------------------------------------------
# Controller principal
# ---------------------------------------------------------------------------

class EnsiasdApiController(http.Controller):
    """Controller REST ENSIASD — toutes les routes /api/v1/..."""

    # ========== ENDPOINTS PUBLICS ==========

    @http.route('/api/v1/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health_check(self):
        """GET /api/v1/health — Vérification de santé (pas d'auth requise)"""
        return json_response({
            'status': 'ok',
            'service': 'ENSIASD API',
            'version': '1.1.0'
        })

    @http.route('/api/v1/info', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    def api_info(self):
        """GET /api/v1/info — Informations sur l'API et les fonctionnalités activées"""
        config = request.env['ensiasd.api.config'].sudo().get_config()
        return json_response({
            'success': True,
            'data': {
                'name': 'ENSIASD Student API',
                'version': '1.1.0',
                'features': {
                    'notes': config.enable_notes,
                    'absences': config.enable_absences,
                    'emploi_temps': config.enable_emploi_temps,
                    'stages': config.enable_stages,
                    'reclamations': 'ensiasd.reclamation' in request.env,
                },
                'modules_optionnels': {
                    'ensiasd_stage': 'ensiasd.stage' in request.env,
                    'ensiasd_timetable': 'ensiasd.seance' in request.env,
                    'ensiasd_reclamation': 'ensiasd.reclamation' in request.env,
                }
            }
        })

    # ========== AUTHENTIFICATION ==========

    @http.route('/api/v1/auth/login', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_key
    @log_request('/auth/login', 'POST')
    def login(self):
        """
        POST /api/v1/auth/login

        Corps JSON requis : { "cne": "...", "password": "..." }
        Retourne un token Bearer valide + données de l'étudiant.

        Note : le mot de passe par défaut est CNE+CIN (ex: K123456+AB789012).
        """
        data, err = _parse_json_body()
        if err:
            return err

        cne = (data.get('cne') or '').strip()
        password = data.get('password') or ''

        if not cne or not password:
            return api_error('CNE et mot de passe requis', 400, 'MISSING_CREDENTIALS')

        student = request.env['ensiasd.student'].sudo().authenticate_api(cne, password)

        if not student:
            # Logger l'échec d'auth sans révéler si le CNE existe
            request.env['ensiasd.api.log'].sudo().log_request(
                endpoint='/auth/login',
                method='POST',
                ip_address=request.httprequest.remote_addr,
                status='auth_failed',
                error_message=f'Échec authentification pour CNE: {cne}'
            )
            return api_error('Identifiants invalides', 401, 'AUTH_FAILED')

        token_data = request.env['ensiasd.api.token'].sudo().create_token(
            student_id=student.id,
            ip_address=request.httprequest.remote_addr,
            user_agent=(
                request.httprequest.user_agent.string[:200]
                if request.httprequest.user_agent else None
            )
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
        """
        POST /api/v1/auth/logout

        Révoque le token Bearer actuel.
        Header requis : Authorization: Bearer <token>
        """
        import hashlib
        auth_header = request.httprequest.headers.get('Authorization')
        token = auth_header[7:] if auth_header and auth_header.startswith('Bearer ') else None

        if token:
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
        """
        POST /api/v1/auth/refresh

        Révoque l'ancien token et génère un nouveau.
        Header requis : Authorization: Bearer <token>
        """
        student = request.student

        token_data = request.env['ensiasd.api.token'].sudo().create_token(
            student_id=student.id,
            ip_address=request.httprequest.remote_addr,
            user_agent=(
                request.httprequest.user_agent.string[:200]
                if request.httprequest.user_agent else None
            )
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
        """
        GET /api/v1/me

        Retourne le profil complet de l'étudiant connecté.
        """
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
        """
        PUT /api/v1/me/password

        Corps JSON : { "old_password": "...", "new_password": "..." }
        Le nouveau mot de passe doit faire au moins 8 caractères.
        """
        data, err = _parse_json_body()
        if err:
            return err

        old_password = data.get('old_password') or ''
        new_password = data.get('new_password') or ''

        if not old_password or not new_password:
            return api_error('Ancien et nouveau mot de passe requis', 400, 'MISSING_FIELDS')

        if len(new_password) < 8:
            return api_error('Le nouveau mot de passe doit faire au moins 8 caractères', 400, 'PASSWORD_TOO_SHORT')

        student = request.student.sudo()

        if not student.check_api_password(old_password):
            return api_error('Ancien mot de passe incorrect', 400, 'WRONG_PASSWORD')

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
        """
        GET /api/v1/notes

        Paramètres optionnels (query string) :
          - annee_id (int) : filtre par année académique
          - module_id (int) : filtre par module
        """
        err = _check_feature('notes')
        if err:
            return err

        student = request.student.sudo()

        annee_id = request.params.get('annee_id')
        module_id = request.params.get('module_id')

        try:
            annee_id = int(annee_id) if annee_id else None
            module_id = int(module_id) if module_id else None
        except (ValueError, TypeError):
            return api_error('annee_id et module_id doivent être des entiers', 400, 'INVALID_PARAMS')

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
        """
        GET /api/v1/notes/summary

        Retourne les moyennes pondérées par module.
        Paramètre optionnel : annee_id (int)
        """
        err = _check_feature('notes')
        if err:
            return err

        student = request.student.sudo()
        annee_id = request.params.get('annee_id')

        try:
            annee_id = int(annee_id) if annee_id else None
        except (ValueError, TypeError):
            return api_error('annee_id doit être un entier', 400, 'INVALID_PARAMS')

        notes = student.get_notes_api(annee_id=annee_id)

        # Calcul des moyennes pondérées par module
        modules = {}
        for note in notes:
            if note.get('module'):
                mod_id = note['module']['id']
                if mod_id not in modules:
                    modules[mod_id] = {
                        'module': note['module'],
                        'notes': [],
                        'total_coef': 0,
                        'total_weighted': 0
                    }
                coef = note.get('coefficient') or 1.0
                valeur = note.get('valeur') or 0.0
                modules[mod_id]['notes'].append(note)
                modules[mod_id]['total_coef'] += coef
                modules[mod_id]['total_weighted'] += valeur * coef

        summary = []
        for mod_data in modules.values():
            if mod_data['total_coef'] > 0:
                moyenne = round(mod_data['total_weighted'] / mod_data['total_coef'], 2)
            else:
                moyenne = 0.0
            summary.append({
                'module': mod_data['module'],
                'moyenne': moyenne,
                'nb_notes': len(mod_data['notes']),
                'notes': mod_data['notes']
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
        """
        GET /api/v1/absences

        Paramètres optionnels (query string) :
          - annee_id (int)
          - date_from (YYYY-MM-DD)
          - date_to   (YYYY-MM-DD)
        """
        err = _check_feature('absences')
        if err:
            return err

        student = request.student.sudo()

        annee_id = request.params.get('annee_id')
        date_from = request.params.get('date_from')
        date_to = request.params.get('date_to')

        try:
            annee_id = int(annee_id) if annee_id else None
        except (ValueError, TypeError):
            return api_error('annee_id doit être un entier', 400, 'INVALID_PARAMS')

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
        """
        GET /api/v1/absences/summary

        Retourne le résumé : total, justifiées, non justifiées.
        """
        err = _check_feature('absences')
        if err:
            return err

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
        """
        GET /api/v1/emploi-temps

        Nécessite le module ensiasd_timetable.
        Paramètres optionnels :
          - date_from (YYYY-MM-DD)
          - date_to   (YYYY-MM-DD)
        """
        err = _check_feature('emploi_temps')
        if err:
            return err

        # Vérification dynamique du module timetable
        err = _model_available('ensiasd.seance')
        if err:
            return err

        student = request.student.sudo()
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
        """
        GET /api/v1/inscriptions

        Paramètre optionnel : annee_id (int)
        """
        student = request.student.sudo()

        annee_id = request.params.get('annee_id')
        try:
            annee_id = int(annee_id) if annee_id else None
        except (ValueError, TypeError):
            return api_error('annee_id doit être un entier', 400, 'INVALID_PARAMS')

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
        """
        GET /api/v1/stages

        Nécessite le module ensiasd_stage.
        """
        err = _check_feature('stages')
        if err:
            return err

        # Vérification dynamique du module stage
        err = _model_available('ensiasd.stage')
        if err:
            return err

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
        """GET /api/v1/annees — Liste des années universitaires"""
        annees = request.env['ensiasd.annee'].sudo().search([])

        data = []
        for a in annees:
            data.append({
                'id': a.id,
                'name': a.name,
                'is_current': a.is_current if hasattr(a, 'is_current') else False,
                'date_debut': a.date_debut.isoformat() if hasattr(a, 'date_debut') and a.date_debut else None,
                'date_fin': a.date_fin.isoformat() if hasattr(a, 'date_fin') and a.date_fin else None,
            })

        return json_response({
            'success': True,
            'data': data
        })

    @http.route('/api/v1/modules', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/modules', 'GET')
    def get_modules(self):
        """GET /api/v1/modules — Liste des modules de l'étudiant connecté"""
        student = request.student.sudo()

        # Récupérer les modules via les inscriptions
        inscriptions = student.get_inscriptions_api()
        modules = [insc['module'] for insc in inscriptions if insc.get('module')]

        return json_response({
            'success': True,
            'data': modules,
            'count': len(modules)
        })

    # ========== RÉCLAMATIONS ==========

    @http.route('/api/v1/reclamations', type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/reclamations', 'GET')
    def get_reclamations(self):
        """
        GET /api/v1/reclamations

        Nécessite le module ensiasd_reclamation.
        Retourne les réclamations de l'étudiant connecté (tri : plus récent en premier).
        Paramètre optionnel : state (draft|soumise|en_cours|traitee|rejetee)
        """
        err = _model_available('ensiasd.reclamation')
        if err:
            return err

        student = request.student.sudo()

        domain = [('student_id', '=', student.id)]

        # Filtre optionnel par état
        state_filter = request.params.get('state')
        valid_states = ['draft', 'soumise', 'en_cours', 'traitee', 'rejetee']
        if state_filter:
            if state_filter not in valid_states:
                return api_error(
                    f"État invalide. Valeurs acceptées : {', '.join(valid_states)}",
                    400, 'INVALID_STATE'
                )
            domain.append(('state', '=', state_filter))

        reclamations = request.env['ensiasd.reclamation'].sudo().search(
            domain, order='date_soumission desc, id desc'
        )

        data = [r.to_api_dict() for r in reclamations]
        return json_response({
            'success': True,
            'data': data,
            'count': len(data)
        })

    @http.route('/api/v1/reclamations', type='http', auth='none', methods=['POST'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/reclamations', 'POST')
    def create_reclamation(self):
        """
        POST /api/v1/reclamations

        Nécessite le module ensiasd_reclamation.
        Corps JSON requis :
          {
            "sujet": "...",
            "description": "...",
            "categorie": "note|absence|pedagogique|administratif|autre",
            "priorite": "0|1"   (optionnel, défaut: "0")
          }
        """
        err = _model_available('ensiasd.reclamation')
        if err:
            return err

        data, err = _parse_json_body()
        if err:
            return err

        student = request.student.sudo()

        sujet = (data.get('sujet') or '').strip()
        description = (data.get('description') or '').strip()
        categorie = data.get('categorie', 'autre')
        priorite = str(data.get('priorite', '0'))

        if not sujet or not description:
            return api_error('Le sujet et la description sont requis', 400, 'MISSING_FIELDS')

        if len(sujet) > 250:
            return api_error('Le sujet ne peut pas dépasser 250 caractères', 400, 'SUJET_TOO_LONG')

        valid_categories = ['note', 'absence', 'pedagogique', 'administratif', 'autre']
        if categorie not in valid_categories:
            return api_error(
                f"Catégorie invalide. Valeurs acceptées : {', '.join(valid_categories)}",
                400, 'INVALID_CATEGORIE'
            )

        if priorite not in ['0', '1']:
            priorite = '0'

        reclamation = request.env['ensiasd.reclamation'].sudo().create({
            'student_id': student.id,
            'sujet': sujet,
            'description': description,
            'categorie': categorie,
            'priorite': priorite,
            'state': 'soumise',
        })

        return json_response({
            'success': True,
            'message': 'Réclamation soumise avec succès',
            'data': reclamation.to_api_dict()
        }, status=201)

    @http.route('/api/v1/reclamations/<int:reclamation_id>',
                type='http', auth='none', methods=['GET'], csrf=False)
    @require_api_key
    @require_token
    @log_request('/reclamations/:id', 'GET')
    def get_reclamation(self, reclamation_id):
        """
        GET /api/v1/reclamations/<id>

        Retourne les détails d'une réclamation spécifique.
        L'étudiant ne peut accéder qu'à ses propres réclamations.
        """
        err = _model_available('ensiasd.reclamation')
        if err:
            return err

        student = request.student.sudo()

        reclamation = request.env['ensiasd.reclamation'].sudo().search([
            ('id', '=', reclamation_id),
            ('student_id', '=', student.id),
        ], limit=1)

        if not reclamation:
            return api_error('Réclamation introuvable', 404, 'NOT_FOUND')

        return json_response({
            'success': True,
            'data': reclamation.to_api_dict()
        })
