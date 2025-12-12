# -*- coding: utf-8 -*-
import hashlib
from odoo import models, fields, api


class EnsiasdStudentApiMixin(models.Model):
    """Extension du modèle étudiant pour l'API"""
    _inherit = 'ensiasd.student'

    # Champ mot de passe pour l'authentification API
    api_password_hash = fields.Char(string='Hash mot de passe API', readonly=True)
    api_enabled = fields.Boolean(string='Accès API activé', default=True)
    last_api_login = fields.Datetime(string='Dernière connexion API')

    def set_api_password(self, password):
        """Définit le mot de passe API de l'étudiant"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.write({'api_password_hash': password_hash})
        return True

    def check_api_password(self, password):
        """Vérifie le mot de passe API"""
        if not self.api_password_hash:
            return False
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.api_password_hash

    def action_set_api_password(self):
        """Ouvre le wizard pour définir le mot de passe API"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Définir mot de passe API',
            'res_model': 'set.api.password.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_student_id': self.id,
            }
        }

    @api.model
    def authenticate_api(self, cne, password):
        """Authentifie un étudiant pour l'API"""
        student = self.search([
            ('cne', '=', cne),
            ('api_enabled', '=', True),
            ('state', 'in', ['inscrit', 'actif']),
        ], limit=1)
        
        if not student:
            return False
        
        if not student.check_api_password(password):
            return False
        
        # Mettre à jour la dernière connexion
        student.write({'last_api_login': fields.Datetime.now()})
        
        return student

    def to_api_dict(self, include_details=False):
        """Convertit l'étudiant en dictionnaire pour l'API"""
        self.ensure_one()
        
        data = {
            'id': self.id,
            'matricule': self.matricule,
            'name': self.name,
            'cne': self.cne,
            'email': self.email,
            'niveau': self.niveau,
            'groupe': {
                'id': self.groupe_id.id,
                'name': self.groupe_id.name,
            } if self.groupe_id else None,
            'state': self.state,
        }
        
        if include_details:
            data.update({
                'cin': self.cin,
                'phone': self.phone,
                'mobile': self.mobile,
                'address': self.address,
                'city': self.city,
                'date_naissance': self.date_naissance.isoformat() if self.date_naissance else None,
                'lieu_naissance': self.lieu_naissance,
                'sexe': self.sexe,
                'nationalite': self.nationalite,
                'annee_courante': {
                    'id': self.annee_courante_id.id,
                    'name': self.annee_courante_id.name,
                } if self.annee_courante_id else None,
            })
        
        return data

    def get_notes_api(self, annee_id=None, module_id=None):
        """Récupère les notes de l'étudiant pour l'API"""
        self.ensure_one()
        
        domain = [('student_id', '=', self.id)]
        if annee_id:
            domain.append(('annee_id', '=', annee_id))
        if module_id:
            domain.append(('module_id', '=', module_id))
        
        notes = self.env['ensiasd.note'].search(domain)
        
        result = []
        for note in notes:
            result.append({
                'id': note.id,
                'module': {
                    'id': note.module_id.id,
                    'code': note.module_id.code,
                    'name': note.module_id.name,
                } if note.module_id else None,
                'type_eval': note.type_eval,
                'valeur': note.valeur,
                'coefficient': note.coefficient,
                'date_eval': note.date_eval.isoformat() if note.date_eval else None,
                'state': note.state,
                'observations': note.observations,
            })
        
        return result

    def get_absences_api(self, annee_id=None, date_from=None, date_to=None):
        """Récupère les absences de l'étudiant pour l'API"""
        self.ensure_one()
        
        domain = [('student_id', '=', self.id)]
        if annee_id:
            domain.append(('annee_id', '=', annee_id))
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        
        absences = self.env['ensiasd.absence'].search(domain)
        
        result = []
        for absence in absences:
            result.append({
                'id': absence.id,
                'date': absence.date.isoformat() if absence.date else None,
                'seance': {
                    'id': absence.seance_id.id,
                    'name': absence.seance_id.name,
                } if hasattr(absence, 'seance_id') and absence.seance_id else None,
                'module': {
                    'id': absence.module_id.id,
                    'code': absence.module_id.code,
                    'name': absence.module_id.name,
                } if hasattr(absence, 'module_id') and absence.module_id else None,
                'justifiee': absence.justifiee if hasattr(absence, 'justifiee') else False,
                'motif': absence.motif if hasattr(absence, 'motif') else None,
            })
        
        return result

    def get_emploi_temps_api(self, date_from=None, date_to=None):
        """Récupère l'emploi du temps de l'étudiant pour l'API"""
        self.ensure_one()
        
        if not self.groupe_id:
            return []
        
        domain = [('groupe_ids', 'in', [self.groupe_id.id])]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        
        seances = self.env['ensiasd.seance'].search(domain, order='date, heure_debut')
        
        result = []
        for seance in seances:
            result.append({
                'id': seance.id,
                'date': seance.date.isoformat() if seance.date else None,
                'heure_debut': seance.heure_debut,
                'heure_fin': seance.heure_fin,
                'element': {
                    'id': seance.element_id.id,
                    'name': seance.element_id.name,
                    'type': seance.element_id.type_element,
                } if seance.element_id else None,
                'module': {
                    'id': seance.element_id.module_id.id,
                    'code': seance.element_id.module_id.code,
                    'name': seance.element_id.module_id.name,
                } if seance.element_id and seance.element_id.module_id else None,
                'salle': {
                    'id': seance.salle_id.id,
                    'code': seance.salle_id.code,
                    'name': seance.salle_id.name,
                } if seance.salle_id else None,
                'enseignant': {
                    'id': seance.enseignant_id.id,
                    'name': seance.enseignant_id.name,
                } if seance.enseignant_id else None,
                'state': seance.state,
            })
        
        return result

    def get_inscriptions_api(self, annee_id=None):
        """Récupère les inscriptions aux modules"""
        self.ensure_one()
        
        domain = [('student_id', '=', self.id)]
        if annee_id:
            domain.append(('annee_id', '=', annee_id))
        
        inscriptions = self.env['ensiasd.inscription'].search(domain)
        
        result = []
        for insc in inscriptions:
            result.append({
                'id': insc.id,
                'module': {
                    'id': insc.module_id.id,
                    'code': insc.module_id.code,
                    'name': insc.module_id.name,
                    'credits_ects': insc.module_id.credits_ects,
                } if insc.module_id else None,
                'annee': {
                    'id': insc.annee_id.id,
                    'name': insc.annee_id.name,
                } if insc.annee_id else None,
                'state': insc.state if hasattr(insc, 'state') else None,
            })
        
        return result

    def get_stages_api(self):
        """Récupère les stages de l'étudiant"""
        self.ensure_one()
        
        stages = self.env['ensiasd.stage'].search([('student_id', '=', self.id)])
        
        result = []
        for stage in stages:
            result.append({
                'id': stage.id,
                'name': stage.name,
                'sujet': stage.sujet,
                'type_stage': stage.type_stage,
                'entreprise': {
                    'id': stage.entreprise_id.id,
                    'name': stage.entreprise_id.name,
                    'city': stage.entreprise_id.city,
                } if stage.entreprise_id else None,
                'date_debut': stage.date_debut.isoformat() if stage.date_debut else None,
                'date_fin': stage.date_fin.isoformat() if stage.date_fin else None,
                'encadrant_interne': {
                    'id': stage.encadrant_interne_id.id,
                    'name': stage.encadrant_interne_id.name,
                } if stage.encadrant_interne_id else None,
                'encadrant_externe': stage.encadrant_externe,
                'state': stage.state,
                'note_finale': stage.note_finale if hasattr(stage, 'note_finale') else None,
                'mention': stage.mention if hasattr(stage, 'mention') else None,
            })
        
        return result
