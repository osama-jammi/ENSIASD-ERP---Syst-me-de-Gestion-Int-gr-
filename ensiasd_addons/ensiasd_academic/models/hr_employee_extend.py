# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Champ pour identifier les enseignants
    is_enseignant = fields.Boolean(
        string='Est enseignant',
        default=False,
        help='Cochez cette case si cet employé est un enseignant'
    )

    # État de l'enseignant
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('active', 'Actif'),
        ('inactive', 'Inactif')
    ], string='État', default='draft', tracking=True)

    # Informations spécifiques aux enseignants
    matricule_enseignant = fields.Char(
        string='Matricule Enseignant',
        help='Matricule unique de l\'enseignant'
    )

    grade = fields.Char(
        string='Grade',
        help='Grade académique (ex: Professeur, Docteur, etc.)'
    )

    specialite = fields.Char(
        string='Spécialité',
        help='Domaine de spécialisation'
    )

    date_recrutement = fields.Date(
        string='Date de recrutement'
    )

    bureau = fields.Char(
        string='Bureau',
        help='Localisation du bureau'
    )

    # Relations avec les entités académiques
    filiere_ids = fields.Many2many(
        'ensiasd.filiere',
        'enseignant_filiere_rel',
        'enseignant_id',
        'filiere_id',
        string='Filières',
        help='Filières dans lesquelles l\'enseignant intervient'
    )

    module_ids = fields.Many2many(
        'ensiasd.module',
        'enseignant_module_rel',
        'enseignant_id',
        'module_id',
        string='Modules',
        compute='_compute_modules',
        store=True,
        help='Modules enseignés (calculé depuis les éléments)'
    )

    element_ids = fields.Many2many(
        'ensiasd.element',
        'enseignant_element_rel',
        'enseignant_id',
        'element_id',
        string='Éléments de module',
        help='Éléments de module que l\'enseignant enseigne'
    )

    # Compteurs
    filiere_count = fields.Integer(
        string='Nombre de filières',
        compute='_compute_counts'
    )

    module_count = fields.Integer(
        string='Nombre de modules',
        compute='_compute_counts'
    )

    element_count = fields.Integer(
        string='Nombre d\'éléments',
        compute='_compute_counts'
    )

    @api.depends('filiere_ids', 'module_ids', 'element_ids')
    def _compute_counts(self):
        for record in self:
            record.filiere_count = len(record.filiere_ids)
            record.module_count = len(record.module_ids)
            record.element_count = len(record.element_ids)

    @api.depends('element_ids', 'element_ids.module_id')
    def _compute_modules(self):
        for record in self:
            if record.element_ids:
                record.module_ids = record.element_ids.mapped('module_id')
            else:
                record.module_ids = False

    @api.constrains('matricule_enseignant', 'is_enseignant')
    def _check_matricule_unique(self):
        for record in self:
            if record.is_enseignant and record.matricule_enseignant:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('matricule_enseignant', '=', record.matricule_enseignant),
                    ('is_enseignant', '=', True)
                ])
                if existing:
                    raise ValidationError(
                        _('Le matricule %s est déjà utilisé par un autre enseignant.')
                        % record.matricule_enseignant
                    )

    # Actions de workflow
    def action_confirm(self):
        """Confirmer l'enseignant"""
        for record in self:
            if not record.matricule_enseignant:
                raise ValidationError(_('Le matricule enseignant est obligatoire pour confirmer.'))
            if not record.grade:
                raise ValidationError(_('Le grade est obligatoire pour confirmer.'))
            record.state = 'confirmed'

    def action_activate(self):
        """Activer l'enseignant"""
        for record in self:
            if record.state != 'confirmed':
                raise ValidationError(_('L\'enseignant doit être confirmé avant d\'être activé.'))
            record.state = 'active'
            record.active = True

    def action_deactivate(self):
        """Désactiver l'enseignant"""
        for record in self:
            record.state = 'inactive'
            record.active = False

    def action_set_to_draft(self):
        """Remettre en brouillon"""
        for record in self:
            record.state = 'draft'

    # Actions smart buttons
    def action_view_filieres(self):
        """Voir les filières de l'enseignant"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Filières'),
            'res_model': 'ensiasd.filiere',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.filiere_ids.ids)],
            'context': {'default_enseignant_id': self.id}
        }

    def action_view_modules(self):
        """Voir les modules de l'enseignant"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Modules'),
            'res_model': 'ensiasd.module',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.module_ids.ids)],
        }

    def action_view_elements(self):
        """Voir les éléments de l'enseignant"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Éléments de module'),
            'res_model': 'ensiasd.element',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.element_ids.ids)],
            'context': {'default_enseignant_id': self.id}
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle resource creation with proper permissions"""
        # Préparer le contexte pour éviter les problèmes
        context = dict(self.env.context or {})
        context.update({
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
            'tracking_disable': True,
        })

        # Always use sudo for employee creation to bypass permission issues
        # with related models (resource, resume, etc.)
        return super(HrEmployee, self.with_context(context).sudo()).create(vals_list)

    def write(self, vals):
        """Override write to handle updates properly"""
        context = dict(self.env.context or {})
        context.update({
            'mail_create_nolog': True,
            'tracking_disable': True,
        })

        # Use sudo for writes that might affect related models
        try:
            return super(HrEmployee, self.with_context(context)).write(vals)
        except (AccessError, Exception) as e:
            # If permission error on related models, use sudo
            if any(model in str(e) for model in ['resource.resource', 'hr.resume.line', 'hr.employee.skill']):
                return super(HrEmployee, self.with_context(context).sudo()).write(vals)
            else:
                raise