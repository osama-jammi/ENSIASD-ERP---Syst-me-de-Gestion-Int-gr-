# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class EnsiasdStudent(models.Model):
    """
    Modèle Étudiant.
    
    OPTION 1 (actuelle): Modèle indépendant avec lien vers res.partner
    OPTION 2: Hériter de res.partner directement (_inherit = 'res.partner')
    
    L'option 1 est choisie pour garder une séparation claire entre
    les étudiants et les autres contacts.
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
    
    # Affectation
    groupe_id = fields.Many2one('ensiasd.groupe', string='Groupe', tracking=True)
    niveau = fields.Selection([
        ('1', '1ère année'),
        ('2', '2ème année'),
        ('3', '3ème année'),
    ], string='Niveau', default='1', tracking=True)
    
    annee_inscription = fields.Many2one('ensiasd.annee', string='Année d\'inscription')
    annee_courante_id = fields.Many2one('ensiasd.annee', string='Année en cours')
    
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('matricule', 'Nouveau') == 'Nouveau':
                vals['matricule'] = self.env['ir.sequence'].next_by_code('ensiasd.student') or 'Nouveau'
            
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
                
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
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

    def action_inscrire(self):
        self.write({'state': 'inscrit'})

    def action_activer(self):
        self.write({'state': 'actif'})

    def action_suspendre(self):
        self.write({'state': 'suspendu'})

    def action_diplomer(self):
        self.write({'state': 'diplome'})
