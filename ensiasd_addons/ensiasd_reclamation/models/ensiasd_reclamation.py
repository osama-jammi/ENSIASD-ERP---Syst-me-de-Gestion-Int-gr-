# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EnsiasdReclamation(models.Model):
    _name = 'ensiasd.reclamation'
    _description = 'Réclamation Étudiant'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_soumission desc, id desc'

    name = fields.Char(string='Référence', readonly=True, copy=False, default='Nouveau')
    
    student_id = fields.Many2one(
        'ensiasd.student',
        string='Étudiant',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    cne = fields.Char(string='CNE', related='student_id.cne', store=True, readonly=True)
    filiere_id = fields.Many2one(
        'ensiasd.filiere',
        string='Filière',
        related='student_id.filiere_id',
        store=True,
        readonly=True
    )
    
    date_soumission = fields.Datetime(
        string='Date de soumission',
        default=fields.Datetime.now,
        readonly=True
    )
    
    categorie = fields.Selection([
        ('note', 'Contestation de note'),
        ('absence', 'Erreur sur absence'),
        ('pedagogique', 'Pédagogique / Cours'),
        ('administratif', 'Administratif'),
        ('autre', 'Autre'),
    ], string='Catégorie', default='note', required=True, tracking=True)
    
    sujet = fields.Char(string='Sujet', required=True, tracking=True)
    description = fields.Text(string='Description détaillée', required=True)
    
    priorite = fields.Selection([
        ('0', 'Normale'),
        ('1', 'Urgente'),
    ], string='Priorité', default='0', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('soumise', 'Soumise'),
        ('en_cours', 'En cours de traitement'),
        ('traitee', 'Traitée'),
        ('rejetee', 'Rejetée'),
    ], string='État', default='draft', tracking=True)
    
    reponse = fields.Text(string='Réponse de la scolarité', tracking=True)
    traite_par = fields.Many2one('res.users', string='Traité par', readonly=True)
    date_traitement = fields.Datetime(string='Date de traitement', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('ensiasd.reclamation') or 'Nouveau'
        return super().create(vals_list)

    def action_soumettre(self):
        """Passe la réclamation à l'état Soumise"""
        for rec in self:
            rec.write({'state': 'soumise'})
        return True

    def action_en_cours(self):
        """Prend en charge la réclamation"""
        for rec in self:
            rec.write({
                'state': 'en_cours',
                'traite_par': self.env.user.id,
            })
        return True

    def action_traiter(self):
        """Marque la réclamation comme traitée avec réponse obligatoire"""
        for rec in self:
            if not rec.reponse:
                raise ValidationError(_("Veuillez renseigner une réponse avant de marquer la réclamation comme traitée."))
            rec.write({
                'state': 'traitee',
                'traite_par': self.env.user.id,
                'date_traitement': fields.Datetime.now(),
            })
        return True

    def action_rejeter(self):
        """Rejette la réclamation avec motif obligatoire"""
        for rec in self:
            if not rec.reponse:
                raise ValidationError(_("Veuillez renseigner un motif de rejet dans le champ Réponse."))
            rec.write({
                'state': 'rejetee',
                'traite_par': self.env.user.id,
                'date_traitement': fields.Datetime.now(),
            })
        return True

    def action_remettre_brouillon(self):
        """Remet la réclamation en brouillon"""
        for rec in self:
            rec.write({'state': 'draft'})
        return True

    def to_api_dict(self):
        """Convertit l'enregistrement en dictionnaire pour l'API REST"""
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'sujet': self.sujet,
            'categorie': self.categorie,
            'categorie_label': dict(self._fields['categorie'].selection).get(self.categorie, self.categorie),
            'description': self.description,
            'priorite': self.priorite,
            'state': self.state,
            'state_label': dict(self._fields['state'].selection).get(self.state, self.state),
            'date_soumission': self.date_soumission.strftime('%Y-%m-%d %H:%M:%S') if self.date_soumission else None,
            'reponse': self.reponse or '',
            'date_traitement': self.date_traitement.strftime('%Y-%m-%d %H:%M:%S') if self.date_traitement else None,
            'traite_par': self.traite_par.name if self.traite_par else None,
        }
