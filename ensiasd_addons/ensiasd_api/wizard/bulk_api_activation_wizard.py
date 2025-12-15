# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class BulkApiActivationWizard(models.TransientModel):
    """
    Assistant pour activer l'API et générer les mots de passe pour plusieurs étudiants
    """
    _name = 'bulk.api.activation.wizard'
    _description = 'Activation API en masse'

    student_ids = fields.Many2many(
        'ensiasd.student',
        string='Étudiants',
        default=lambda self: self._default_students()
    )

    activate_api = fields.Boolean(
        string='Activer l\'accès API',
        default=True
    )

    regenerate_passwords = fields.Boolean(
        string='Régénérer les mots de passe',
        default=True,
        help="Génère ou régénère les mots de passe (CNE+CIN)"
    )

    only_missing_passwords = fields.Boolean(
        string='Uniquement ceux sans mot de passe',
        default=True
    )

    # Statistiques
    total_students = fields.Integer(
        string='Total étudiants',
        compute='_compute_stats'
    )

    with_cne_cin = fields.Integer(
        string='Avec CNE et CIN',
        compute='_compute_stats'
    )

    without_password = fields.Integer(
        string='Sans mot de passe API',
        compute='_compute_stats'
    )

    already_active = fields.Integer(
        string='API déjà active',
        compute='_compute_stats'
    )

    def _default_students(self):
        """Récupère les étudiants sélectionnés dans la vue liste"""
        return self.env.context.get('active_ids', [])

    @api.depends('student_ids')
    def _compute_stats(self):
        for wizard in self:
            wizard.total_students = len(wizard.student_ids)
            wizard.with_cne_cin = len(wizard.student_ids.filtered(lambda s: s.cne and s.cin))
            wizard.without_password = len(wizard.student_ids.filtered(lambda s: not s.api_password_hash))
            wizard.already_active = len(wizard.student_ids.filtered(lambda s: s.api_enabled))

    def action_activate(self):
        """
        Active l'API et génère les mots de passe pour les étudiants sélectionnés
        """
        self.ensure_one()

        if not self.student_ids:
            raise UserError("Aucun étudiant sélectionné!")

        success_count = 0
        error_count = 0
        errors = []

        for student in self.student_ids:
            try:
                # Vérifier que CNE et CIN sont présents
                if not student.cne or not student.cin:
                    errors.append(f"{student.name}: CNE ou CIN manquant")
                    error_count += 1
                    continue

                # Activer l'API si demandé
                if self.activate_api and not student.api_enabled:
                    student.write({'api_enabled': True})

                # Générer/régénérer le mot de passe
                should_generate = False

                if self.regenerate_passwords:
                    if self.only_missing_passwords:
                        # Seulement si pas de mot de passe
                        should_generate = not student.api_password_hash
                    else:
                        # Toujours régénérer
                        should_generate = True

                if should_generate:
                    password = student._generate_auto_password(student.cne, student.cin)
                    student.set_api_password(password)

                    # Logger dans le chatter
                    student.message_post(
                        body=f"Mot de passe API généré automatiquement (CNE+CIN)",
                        subject="Activation API en masse"
                    )

                success_count += 1

            except Exception as e:
                errors.append(f"{student.name}: {str(e)}")
                error_count += 1

        # Message de résultat
        message = f"""
        <h4>Activation API terminée</h4>
        <ul>
            <li><strong>{success_count}</strong> étudiant(s) traité(s) avec succès</li>
            <li><strong>{error_count}</strong> erreur(s)</li>
        </ul>
        """

        if errors:
            message += "<h5>Erreurs:</h5><ul>"
            for error in errors[:10]:  # Limiter à 10 erreurs
                message += f"<li>{error}</li>"
            if len(errors) > 10:
                message += f"<li>... et {len(errors) - 10} autres erreurs</li>"
            message += "</ul>"

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Activation API',
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }

    def action_export_credentials(self):
        """
        Exporte un fichier CSV avec les identifiants API
        ATTENTION: À utiliser avec précaution!
        """
        self.ensure_one()

        import base64
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # En-tête
        writer.writerow(['Matricule', 'Nom', 'CNE', 'Email', 'Login API', 'Mot de passe API', 'Statut'])

        # Données
        for student in self.student_ids.filtered(lambda s: s.cne and s.cin and s.api_enabled):
            password = f"{student.cne}+{student.cin}"
            writer.writerow([
                student.matricule,
                student.name,
                student.cne,
                student.email or '',
                student.cne,  # Login = CNE
                password,
                'Actif' if student.api_password_hash else 'Non configuré'
            ])

        # Créer le fichier
        csv_data = output.getvalue()
        csv_base64 = base64.b64encode(csv_data.encode('utf-8'))

        # Créer l'attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'identifiants_api_etudiants.csv',
            'type': 'binary',
            'datas': csv_base64,
            'mimetype': 'text/csv',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }