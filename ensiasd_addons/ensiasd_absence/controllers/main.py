# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class AbsenceController(http.Controller):
    """
    Contrôleur pour le formulaire d'appel en ligne
    """

    @http.route('/absence/appel/<string:token>', type='http', auth='public', website=True)
    def appel_form(self, token, **kwargs):
        """Afficher le formulaire d'appel"""
        Token = request.env['ensiasd.absence.token'].sudo()
        
        # Vérifier le token
        token_record = Token.search([('token', '=', token)], limit=1)
        
        if not token_record:
            return request.render('ensiasd_absence.appel_error', {
                'error': 'Lien invalide ou expiré.'
            })
        
        if not token_record.is_valid():
            return request.render('ensiasd_absence.appel_error', {
                'error': 'Ce lien a expiré ou a déjà été utilisé.'
            })
        
        seance = token_record.seance_id
        
        # Récupérer les étudiants
        students = request.env['ensiasd.student'].sudo()
        for groupe in seance.groupe_ids:
            students |= groupe.student_ids.filtered(lambda s: s.state == 'actif')
        
        # Récupérer les absences existantes
        existing_absences = request.env['ensiasd.absence'].sudo().search([
            ('seance_id', '=', seance.id)
        ])
        absent_ids = existing_absences.mapped('student_id.id')
        
        return request.render('ensiasd_absence.appel_form', {
            'seance': seance,
            'students': students.sorted(key=lambda s: s.name),
            'absent_ids': absent_ids,
            'token': token,
        })

    @http.route('/absence/appel/submit', type='http', auth='public', website=True, methods=['POST'])
    def appel_submit(self, **post):
        """Soumettre le formulaire d'appel"""
        token = post.get('token')
        
        Token = request.env['ensiasd.absence.token'].sudo()
        token_record = Token.search([('token', '=', token)], limit=1)
        
        if not token_record or not token_record.is_valid():
            return request.render('ensiasd_absence.appel_error', {
                'error': 'Lien invalide ou expiré.'
            })
        
        seance = token_record.seance_id
        Absence = request.env['ensiasd.absence'].sudo()
        
        # Supprimer les absences existantes
        existing = Absence.search([('seance_id', '=', seance.id)])
        existing.unlink()
        
        # Créer les nouvelles absences
        absent_count = 0
        for key, value in post.items():
            if key.startswith('student_') and value == 'absent':
                student_id = int(key.replace('student_', ''))
                Absence.create({
                    'student_id': student_id,
                    'seance_id': seance.id,
                    'state': 'absent',
                })
                absent_count += 1
        
        # Marquer le token comme utilisé
        token_record.mark_used()
        
        # Marquer la séance comme appel fait
        seance.sudo().write({
            'appel_fait': True,
            'date_appel': request.env['fields'].Datetime.now(),
            'state': 'done',
        })
        
        return request.render('ensiasd_absence.appel_success', {
            'seance': seance,
            'absent_count': absent_count,
            'total': len(seance.groupe_ids.mapped('student_ids').filtered(lambda s: s.state == 'actif')),
        })

    @http.route('/absence/justification/<int:absence_id>', type='http', auth='public', website=True)
    def justification_form(self, absence_id, **kwargs):
        """Formulaire de justification d'absence"""
        absence = request.env['ensiasd.absence'].sudo().browse(absence_id)
        
        if not absence.exists():
            return request.render('ensiasd_absence.appel_error', {
                'error': 'Absence non trouvée.'
            })
        
        return request.render('ensiasd_absence.justification_form', {
            'absence': absence,
        })

    @http.route('/absence/justification/submit', type='http', auth='public', website=True, methods=['POST'])
    def justification_submit(self, **post):
        """Soumettre une justification"""
        absence_id = int(post.get('absence_id', 0))
        motif = post.get('motif', '')
        justificatif = post.get('justificatif')
        
        absence = request.env['ensiasd.absence'].sudo().browse(absence_id)
        
        if not absence.exists():
            return request.render('ensiasd_absence.appel_error', {
                'error': 'Absence non trouvée.'
            })
        
        vals = {
            'motif': motif,
            'state': 'pending',
            'date_justification': request.env['fields'].Datetime.now(),
        }
        
        if justificatif:
            import base64
            vals['justificatif'] = base64.b64encode(justificatif.read())
            vals['justificatif_filename'] = justificatif.filename
        
        absence.write(vals)
        
        return request.render('ensiasd_absence.justification_success', {
            'absence': absence,
        })
