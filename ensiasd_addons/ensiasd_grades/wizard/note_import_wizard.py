# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api
from odoo.exceptions import UserError


class NoteImportWizard(models.TransientModel):
    """
    Assistant d'import des notes depuis un fichier Excel/CSV
    """
    _name = 'ensiasd.note.import.wizard'
    _description = 'Assistant d\'import des notes'

    session_id = fields.Many2one(
        'ensiasd.session',
        string='Session',
        required=True,
        domain=[('state', 'in', ['open', 'saisie'])]
    )
    
    module_id = fields.Many2one(
        'ensiasd.module',
        string='Module',
        required=True
    )
    
    type_eval = fields.Selection([
        ('cc1', 'CC 1'),
        ('cc2', 'CC 2'),
        ('cc3', 'CC 3'),
        ('tp', 'TP'),
        ('projet', 'Projet'),
        ('examen', 'Examen'),
        ('rattrapage', 'Rattrapage'),
    ], string='Type d\'évaluation', required=True)
    
    file = fields.Binary(string='Fichier', required=True)
    filename = fields.Char(string='Nom du fichier')
    
    file_type = fields.Selection([
        ('csv', 'CSV'),
        ('xlsx', 'Excel (XLSX)'),
    ], string='Format', default='xlsx', required=True)
    
    delimiter = fields.Selection([
        (',', 'Virgule (,)'),
        (';', 'Point-virgule (;)'),
        ('\t', 'Tabulation'),
    ], string='Délimiteur CSV', default=';')
    
    skip_header = fields.Boolean(
        string='Ignorer la première ligne',
        default=True,
        help="Cocher si le fichier contient une ligne d'en-tête"
    )
    
    column_cne = fields.Integer(
        string='Colonne CNE',
        default=1,
        help="Numéro de la colonne contenant le CNE (commençant à 1)"
    )
    
    column_note = fields.Integer(
        string='Colonne Note',
        default=2,
        help="Numéro de la colonne contenant la note"
    )
    
    # Résultats
    import_count = fields.Integer(
        string='Notes importées',
        readonly=True
    )
    
    error_count = fields.Integer(
        string='Erreurs',
        readonly=True
    )
    
    error_log = fields.Text(
        string='Log des erreurs',
        readonly=True
    )
    
    state = fields.Selection([
        ('draft', 'Configuration'),
        ('preview', 'Aperçu'),
        ('done', 'Terminé'),
    ], string='État', default='draft')

    def action_preview(self):
        """Aperçu des données à importer"""
        self.ensure_one()
        
        if not self.file:
            raise UserError("Veuillez sélectionner un fichier!")
        
        # Lire le fichier
        file_content = base64.b64decode(self.file)
        
        try:
            if self.file_type == 'csv':
                data = self._parse_csv(file_content)
            else:
                data = self._parse_xlsx(file_content)
        except Exception as e:
            raise UserError(f"Erreur lors de la lecture du fichier: {str(e)}")
        
        # Afficher un aperçu
        self.error_log = f"Fichier lu avec succès.\n{len(data)} lignes trouvées."
        self.state = 'preview'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        """Importer les notes"""
        self.ensure_one()
        
        if not self.file:
            raise UserError("Veuillez sélectionner un fichier!")
        
        # Lire le fichier
        file_content = base64.b64decode(self.file)
        
        try:
            if self.file_type == 'csv':
                data = self._parse_csv(file_content)
            else:
                data = self._parse_xlsx(file_content)
        except Exception as e:
            raise UserError(f"Erreur lors de la lecture du fichier: {str(e)}")
        
        # Importer les notes
        imported = 0
        errors = []
        
        for i, row in enumerate(data, start=1):
            try:
                cne = str(row[self.column_cne - 1]).strip()
                note_value = row[self.column_note - 1]
                
                # Chercher l'étudiant
                student = self.env['ensiasd.student'].search([('cne', '=', cne)], limit=1)
                if not student:
                    errors.append(f"Ligne {i}: CNE '{cne}' non trouvé")
                    continue
                
                # Chercher l'inscription
                inscription = self.env['ensiasd.inscription'].search([
                    ('student_id', '=', student.id),
                    ('module_id', '=', self.module_id.id),
                    ('annee_id', '=', self.session_id.annee_id.id),
                ], limit=1)
                
                if not inscription:
                    errors.append(f"Ligne {i}: Pas d'inscription pour {cne} au module {self.module_id.code}")
                    continue
                
                # Convertir la note
                try:
                    note_value = float(str(note_value).replace(',', '.'))
                except:
                    errors.append(f"Ligne {i}: Note invalide '{note_value}'")
                    continue
                
                # Créer ou mettre à jour la note
                existing = self.env['ensiasd.note.element'].search([
                    ('inscription_id', '=', inscription.id),
                    ('type_eval', '=', self.type_eval),
                    ('session_id', '=', self.session_id.id),
                ], limit=1)
                
                if existing:
                    existing.write({'valeur': note_value})
                else:
                    self.env['ensiasd.note.element'].create({
                        'inscription_id': inscription.id,
                        'element_id': self.module_id.element_ids[0].id if self.module_id.element_ids else False,
                        'type_eval': self.type_eval,
                        'session_id': self.session_id.id,
                        'valeur': note_value,
                    })
                
                imported += 1
                
            except Exception as e:
                errors.append(f"Ligne {i}: Erreur - {str(e)}")
        
        # Mettre à jour le wizard
        self.write({
            'import_count': imported,
            'error_count': len(errors),
            'error_log': '\n'.join(errors) if errors else 'Import réussi sans erreur.',
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _parse_csv(self, file_content):
        """Parser un fichier CSV"""
        import csv
        
        content = file_content.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(content), delimiter=self.delimiter)
        
        data = list(reader)
        if self.skip_header and data:
            data = data[1:]
        
        return data

    def _parse_xlsx(self, file_content):
        """Parser un fichier Excel"""
        try:
            import openpyxl
        except ImportError:
            raise UserError("Le module openpyxl n'est pas installé. Veuillez l'installer pour lire les fichiers Excel.")
        
        workbook = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True)
        sheet = workbook.active
        
        data = []
        for i, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if self.skip_header and i == 1:
                continue
            data.append(list(row))
        
        return data

    def action_download_template(self):
        """Télécharger un modèle de fichier"""
        # Créer un modèle CSV
        template = "CNE;Note\n"
        
        # Ajouter les étudiants inscrits
        inscriptions = self.env['ensiasd.inscription'].search([
            ('module_id', '=', self.module_id.id),
            ('annee_id', '=', self.session_id.annee_id.id),
            ('state', '=', 'validated'),
        ])
        
        for inscription in inscriptions:
            template += f"{inscription.student_id.cne};\n"
        
        # Encoder et retourner
        file_content = base64.b64encode(template.encode('utf-8'))
        
        attachment = self.env['ir.attachment'].create({
            'name': f'modele_notes_{self.module_id.code}.csv',
            'type': 'binary',
            'datas': file_content,
            'mimetype': 'text/csv',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
