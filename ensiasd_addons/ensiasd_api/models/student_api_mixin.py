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

    @api.model_create_multi
    def create(self, vals_list):
        """
        Surcharge de create pour générer automatiquement le mot de passe API
        si api_enabled est True et que CNE + CIN sont fournis
        """
        records = super().create(vals_list)

        for record in records:
            # Générer le mot de passe API automatiquement si activé
            if record.api_enabled and record.cne and record.cin:
                auto_password = self._generate_auto_password(record.cne, record.cin)
                record.set_api_password(auto_password)

                # Logger l'événement
                record.message_post(
                    body=f"Mot de passe API généré automatiquement (CNE+CIN)",
                    subject="Activation API"
                )

        return records

    def write(self, vals):
        """
        Surcharge de write pour régénérer le mot de passe si CNE ou CIN change
        """
        res = super().write(vals)

        # Si CNE ou CIN change et que l'API est activée
        if ('cne' in vals or 'cin' in vals) and self.api_enabled:
            for record in self:
                if record.cne and record.cin and not record.api_password_hash:
                    auto_password = self._generate_auto_password(record.cne, record.cin)
                    record.set_api_password(auto_password)

        # Si api_enabled passe à True et pas encore de mot de passe
        if vals.get('api_enabled') and not self.api_password_hash:
            for record in self:
                if record.cne and record.cin:
                    auto_password = self._generate_auto_password(record.cne, record.cin)
                    record.set_api_password(auto_password)

        return res

    @api.model
    def _generate_auto_password(self, cne, cin):
        """
        Génère un mot de passe automatique basé sur CNE + CIN
        Format: CNE+CIN (ex: K1234567+AB123456)

        Args:
            cne (str): Code National Étudiant
            cin (str): Carte d'Identité Nationale

        Returns:
            str: Mot de passe généré
        """
        # Nettoyer les espaces
        cne = str(cne).strip() if cne else ''
        cin = str(cin).strip() if cin else ''

        # Format: CNE+CIN
        password = f"{cne}+{cin}"

        return password

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

    def action_regenerate_api_password(self):
        """
        Action pour régénérer le mot de passe API
        Accessible depuis l'interface
        """
        self.ensure_one()

        if not self.cne or not self.cin:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erreur',
                    'message': 'CNE et CIN requis pour générer le mot de passe',
                    'type': 'danger',
                }
            }

        # Générer le nouveau mot de passe
        new_password = self._generate_auto_password(self.cne, self.cin)
        self.set_api_password(new_password)

        # Message de confirmation avec le mot de passe (ATTENTION: à ne montrer qu'une fois!)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Mot de passe régénéré',
                'message': f'Nouveau mot de passe API: {new_password}',
                'type': 'success',
                'sticky': True,  # Reste affiché
            }
        }

    def action_show_api_credentials(self):
        """
        Affiche les identifiants API de l'étudiant
        (Utile pour le support)
        """
        self.ensure_one()

        if not self.api_enabled:
            message = "L'accès API n'est pas activé pour cet étudiant"
        elif not self.api_password_hash:
            message = "Aucun mot de passe API défini. Utilisez 'Régénérer mot de passe API'"
        else:
            # Ne jamais afficher le vrai mot de passe!
            message = f"""
            Identifiants API:
            - CNE: {self.cne}
            - Mot de passe: CNE+CIN (Format: {self.cne}+{self.cin if self.cin else 'XXXX'})
            - Statut: {'Actif' if self.api_enabled else 'Inactif'}
            - Dernière connexion: {self.last_api_login or 'Jamais'}
            """

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Identifiants API',
                'message': message,
                'type': 'info',
                'sticky': True,
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

        # Vérifier si le module grades est installé
        if 'ensiasd.note' not in self.env:
            return []

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
                'type_eval': note.type_eval if hasattr(note, 'type_eval') else None,
                'valeur': note.note_finale,
                'coefficient': note.module_id.coefficient if hasattr(note.module_id, 'coefficient') else 1.0,
                'date_eval': note.date.isoformat() if hasattr(note, 'date') and note.date else None,
                'state': note.state,
                'observations': note.observations if hasattr(note, 'observations') else None,
            })

        return result

    def get_absences_api(self, annee_id=None, date_from=None, date_to=None):
        """Récupère les absences de l'étudiant pour l'API"""
        self.ensure_one()

        # Vérifier si le module absence est installé
        if 'ensiasd.absence' not in self.env:
            return []

        domain = [('student_id', '=', self.id)]
        if annee_id:
            # Filtrer par année via les séances
            domain.append(('seance_id.emploi_id.annee_id', '=', annee_id))
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
                } if absence.seance_id else None,
                'module': {
                    'id': absence.module_id.id,
                    'code': absence.module_id.code,
                    'name': absence.module_id.name,
                } if absence.module_id else None,
                'justifiee': absence.justifiee if hasattr(absence, 'justifiee') else False,
                'motif': absence.motif if hasattr(absence, 'motif') else None,
                'state': absence.state if hasattr(absence, 'state') else 'absent',
            })

        return result

    def get_emploi_temps_api(self, date_from=None, date_to=None):
        """Récupère l'emploi du temps de l'étudiant pour l'API"""
        self.ensure_one()

        # Vérifier si le module timetable est installé
        if 'ensiasd.seance' not in self.env:
            return []

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
                    'credits_ects': insc.module_id.credits_ects if hasattr(insc.module_id, 'credits_ects') else 0,
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

        # Vérifier si le module stages est installé
        if 'ensiasd.stage' not in self.env:
            return []

        stages = self.env['ensiasd.stage'].search([('student_id', '=', self.id)])

        result = []
        for stage in stages:
            result.append({
                'id': stage.id,
                'name': stage.name,
                'sujet': stage.sujet if hasattr(stage, 'sujet') else None,
                'type_stage': stage.type_stage if hasattr(stage, 'type_stage') else None,
                'entreprise': {
                    'id': stage.entreprise_id.id,
                    'name': stage.entreprise_id.name,
                    'city': stage.entreprise_id.city,
                } if hasattr(stage, 'entreprise_id') and stage.entreprise_id else None,
                'date_debut': stage.date_debut.isoformat() if hasattr(stage,
                                                                      'date_debut') and stage.date_debut else None,
                'date_fin': stage.date_fin.isoformat() if hasattr(stage, 'date_fin') and stage.date_fin else None,
                'encadrant_interne': {
                    'id': stage.encadrant_interne_id.id,
                    'name': stage.encadrant_interne_id.name,
                } if hasattr(stage, 'encadrant_interne_id') and stage.encadrant_interne_id else None,
                'encadrant_externe': stage.encadrant_externe if hasattr(stage, 'encadrant_externe') else None,
                'state': stage.state if hasattr(stage, 'state') else None,
                'note_finale': stage.note_finale if hasattr(stage, 'note_finale') else None,
                'mention': stage.mention if hasattr(stage, 'mention') else None,
            })

        return result