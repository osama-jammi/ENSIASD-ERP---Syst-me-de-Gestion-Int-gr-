# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EnsiasdStudent(models.Model):
    """
    Modèle Étudiant avec inscription automatique à la filière et aux modules
    """
    _name = 'ensiasd.student'
    _description = 'Étudiant ENSIASD'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Lien vers res.partner (module Contacts)
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact associé',
        ondelete='cascade',
        help="Lien vers le carnet d'adresses Odoo"
    )

    name = fields.Char(string='Nom complet', required=True, tracking=True)

    # Identifiants
    cne = fields.Char(string='CNE', required=True, tracking=True)
    cin = fields.Char(string='CIN', tracking=True)
    matricule = fields.Char(string='Matricule', readonly=True, copy=False, default='Nouveau')

    # Contact
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Téléphone')
    mobile = fields.Char(string='Mobile')
    address = fields.Text(string='Adresse')
    city = fields.Char(string='Ville')

    # Informations personnelles
    date_naissance = fields.Date(string='Date de naissance')
    lieu_naissance = fields.Char(string='Lieu de naissance')
    sexe = fields.Selection([('male', 'Masculin'), ('female', 'Féminin')], string='Sexe')
    nationalite = fields.Char(string='Nationalité', default='Marocaine')
    image = fields.Binary(string='Photo', attachment=True)

    # Filière
    filiere_id = fields.Many2one(
        'ensiasd.filiere',
        string='Filière',
        required=True,
        tracking=True,
        help="Filière d'inscription de l'étudiant"
    )

    # Affectation
    groupe_id = fields.Many2one('ensiasd.groupe', string='Groupe', tracking=True)
    niveau = fields.Selection([
        ('1', '1ère année'),
        ('2', '2ème année'),
        ('3', '3ème année'),
    ], string='Niveau', default='1', tracking=True)

    annee_inscription = fields.Many2one(
        'ensiasd.annee',
        string='Année d\'inscription',
        required=True,
        default=lambda self: self._get_current_annee()
    )

    annee_courante_id = fields.Many2one(
        'ensiasd.annee',
        string='Année en cours',
        default=lambda self: self._get_current_annee()
    )

    # Inscriptions aux modules
    inscription_ids = fields.One2many(
        'ensiasd.inscription',
        'student_id',
        string='Inscriptions aux modules'
    )

    inscription_count = fields.Integer(
        string='Nombre d\'inscriptions',
        compute='_compute_inscription_count'
    )

    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('inscrit', 'Inscrit'),
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('diplome', 'Diplômé'),
        ('abandon', 'Abandon'),
    ], string='État', default='draft', tracking=True)

    active = fields.Boolean(string='Actif', default=True)

    # Contact d'urgence
    contact_urgence_nom = fields.Char(string='Contact d\'urgence')
    contact_urgence_tel = fields.Char(string='Téléphone urgence')

    _sql_constraints = [
        ('cne_unique', 'UNIQUE(cne)', 'Ce CNE existe déjà!'),
        ('cin_unique', 'UNIQUE(cin)', 'Ce CIN existe déjà!'),
    ]

    def _get_current_annee(self):
        """Récupérer l'année académique courante"""
        config = self.env['ensiasd.config'].sudo().search([], limit=1)
        if config and config.annee_courante_id:
            return config.annee_courante_id.id

        # Si pas de config, essayer de trouver une année active
        annee = self.env['ensiasd.annee'].search([('state', '=', 'en_cours')], limit=1)
        if annee:
            return annee.id

        return False

    @api.depends('inscription_ids')
    def _compute_inscription_count(self):
        for record in self:
            record.inscription_count = len(record.inscription_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Générer le matricule
            if vals.get('matricule', 'Nouveau') == 'Nouveau':
                vals['matricule'] = self.env['ir.sequence'].next_by_code('ensiasd.student') or 'Nouveau'

            # S'assurer que annee_courante_id est défini
            if not vals.get('annee_courante_id'):
                current_annee = self._get_current_annee()
                if current_annee:
                    vals['annee_courante_id'] = current_annee
                    # Mettre aussi annee_inscription si non défini
                    if not vals.get('annee_inscription'):
                        vals['annee_inscription'] = current_annee

            # Créer automatiquement un contact res.partner
            if not vals.get('partner_id'):
                partner = self.env['res.partner'].create({
                    'name': vals.get('name'),
                    'email': vals.get('email'),
                    'phone': vals.get('phone'),
                    'mobile': vals.get('mobile'),
                    'is_company': False,
                    'type': 'contact',
                    'comment': f"Étudiant ENSIASD - CNE: {vals.get('cne')}",
                })
                vals['partner_id'] = partner.id

        records = super().create(vals_list)

        # Inscription automatique aux modules de 1ère année
        for record in records:
            if record.filiere_id and record.niveau == '1' and record.annee_courante_id:
                record._auto_inscribe_modules()

        return records

    def write(self, vals):
        # Gestion du changement de filière
        old_filiere = {record.id: record.filiere_id for record in self}

        res = super().write(vals)

        # Si changement de filière, notifier
        if 'filiere_id' in vals:
            for record in self:
                if old_filiere.get(record.id) != record.filiere_id:
                    record.message_post(
                        body=f"Changement de filière: {old_filiere.get(record.id).name if old_filiere.get(record.id) else 'Aucune'} → {record.filiere_id.name}",
                        subject="Changement de filière"
                    )

        # Synchroniser avec res.partner
        for record in self:
            if record.partner_id:
                partner_vals = {}
                if 'name' in vals:
                    partner_vals['name'] = vals['name']
                if 'email' in vals:
                    partner_vals['email'] = vals['email']
                if 'phone' in vals:
                    partner_vals['phone'] = vals['phone']
                if partner_vals:
                    record.partner_id.write(partner_vals)

        return res

    def _auto_inscribe_modules(self):
        """
        Inscription automatique aux modules de 1ère année de la filière
        """
        self.ensure_one()

        if not self.filiere_id:
            raise ValidationError("Veuillez sélectionner une filière avant d'inscrire l'étudiant.")

        if not self.annee_courante_id:
            raise ValidationError(
                "L'année académique courante n'est pas définie. Veuillez configurer l'année courante dans la configuration ENSIASD.")

        # Chercher les modules de S1 et S2 (1ère année)
        modules = self.env['ensiasd.module'].search([
            ('filiere_id', '=', self.filiere_id.id),
            ('semestre', 'in', ['S1', 'S2']),
            ('type_module', '=', 'obligatoire'),
            ('active', '=', True)
        ])

        if not modules:
            self.message_post(
                body=f"Aucun module obligatoire trouvé pour la 1ère année de la filière {self.filiere_id.name}",
                subject="Information"
            )
            return

        # Créer les inscriptions
        inscriptions_created = 0
        for module in modules:
            # Vérifier si pas déjà inscrit
            existing = self.env['ensiasd.inscription'].search([
                ('student_id', '=', self.id),
                ('module_id', '=', module.id),
                ('annee_id', '=', self.annee_courante_id.id)
            ])

            if not existing:
                try:
                    self.env['ensiasd.inscription'].create({
                        'student_id': self.id,
                        'module_id': module.id,
                        'annee_id': self.annee_courante_id.id,
                        'state': 'confirmed',
                        'date_inscription': fields.Date.today(),
                    })
                    inscriptions_created += 1
                except Exception as e:
                    raise ValidationError(
                        f"Erreur lors de l'inscription au module {module.code}: {str(e)}"
                    )

        # Message de confirmation
        if inscriptions_created > 0:
            self.message_post(
                body=f"Inscription automatique à {inscriptions_created} modules de 1ère année ({self.filiere_id.name})",
                subject="Inscription automatique"
            )
        else:
            self.message_post(
                body=f"L'étudiant était déjà inscrit aux modules de 1ère année",
                subject="Information"
            )

    def action_inscrire(self):
        """Passer à l'état inscrit + inscription automatique aux modules"""
        for record in self:
            # Vérifier que l'année courante est définie
            if not record.annee_courante_id:
                raise ValidationError(
                    "L'année académique courante n'est pas définie. "
                    "Veuillez la définir dans la fiche de l'étudiant."
                )

            record.write({'state': 'inscrit'})

            # Inscription automatique si pas encore fait
            if not record.inscription_ids:
                record._auto_inscribe_modules()

    def action_activer(self):
        """Activer l'étudiant"""
        self.write({'state': 'actif'})

    def action_suspendre(self):
        """Suspendre l'étudiant"""
        self.write({'state': 'suspendu'})

    def action_diplomer(self):
        """Diplômer l'étudiant"""
        self.write({'state': 'diplome'})

    def action_view_inscriptions(self):
        """Voir les inscriptions aux modules"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Inscriptions - {self.name}',
            'res_model': 'ensiasd.inscription',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {
                'default_student_id': self.id,
                'default_annee_id': self.annee_courante_id.id if self.annee_courante_id else False,
            },
        }

    def action_inscribe_next_year(self):
        """
        Réinscription pour l'année suivante
        Inscrit aux modules de l'année supérieure
        """
        self.ensure_one()

        # Vérifications
        if not self.annee_courante_id:
            raise ValidationError("L'année académique courante n'est pas définie.")

        if self.state not in ['actif', 'inscrit']:
            raise ValidationError("Seuls les étudiants actifs ou inscrits peuvent être réinscrits.")

        if self.niveau == '3':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Information',
                    'message': 'Étudiant en dernière année. Veuillez le diplômer au lieu de le réinscrire.',
                    'type': 'info',
                }
            }

        # Passer au niveau supérieur
        next_level = str(int(self.niveau) + 1)

        # Déterminer les semestres
        semestre_map = {
            '2': ['S3', 'S4'],
            '3': ['S5', 'S6'],
        }

        semestres = semestre_map.get(next_level, [])

        if not semestres:
            raise ValidationError(f"Impossible de déterminer les semestres pour le niveau {next_level}.")

        # Chercher les modules
        modules = self.env['ensiasd.module'].search([
            ('filiere_id', '=', self.filiere_id.id),
            ('semestre', 'in', semestres),
            ('type_module', '=', 'obligatoire'),
            ('active', '=', True)
        ])

        if not modules:
            raise ValidationError(
                f"Aucun module obligatoire trouvé pour le niveau {next_level} "
                f"(semestres {', '.join(semestres)}) de la filière {self.filiere_id.name}."
            )

        # Créer les inscriptions
        inscriptions_created = 0
        errors = []

        for module in modules:
            # Vérifier si pas déjà inscrit
            existing = self.env['ensiasd.inscription'].search([
                ('student_id', '=', self.id),
                ('module_id', '=', module.id),
                ('annee_id', '=', self.annee_courante_id.id)
            ])

            if not existing:
                try:
                    self.env['ensiasd.inscription'].create({
                        'student_id': self.id,
                        'module_id': module.id,
                        'annee_id': self.annee_courante_id.id,
                        'state': 'confirmed',
                        'date_inscription': fields.Date.today(),
                    })
                    inscriptions_created += 1
                except Exception as e:
                    errors.append(f"Module {module.code}: {str(e)}")

        if errors:
            raise ValidationError(
                f"Erreurs lors de l'inscription:\n" + "\n".join(errors)
            )

        # Mettre à jour le niveau
        self.niveau = next_level

        # Message de confirmation
        self.message_post(
            body=f"Réinscription en {next_level}ère année - {inscriptions_created} modules ajoutés",
            subject="Réinscription année supérieure"
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Réinscription effectuée',
                'message': f'Passage en {next_level}ère année. {inscriptions_created} modules ajoutés.',
                'type': 'success',
                'sticky': False,
            }
        }