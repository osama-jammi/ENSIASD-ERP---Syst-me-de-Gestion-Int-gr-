# -*- coding: utf-8 -*-
import hashlib

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestApiToken(TransactionCase):
    """
    Non-régression pour la suppression du champ token en clair sur
    ensiasd.api.token : l'authentification doit continuer à fonctionner
    en ne s'appuyant que sur token_hash.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.annee = cls.env['ensiasd.annee'].create({
            'name': 'Année Test 2024-2025',
            'code': 'ATEST2425-API',
            'date_debut': '2024-09-01',
            'date_fin': '2025-07-31',
            'is_current': True,
            'state': 'open',
        })

        cls.filiere = cls.env['ensiasd.filiere'].create({
            'name': 'Filière Test API',
            'code': 'FTESTAPI',
        })

        # annee_inscription / annee_courante_id fournis explicitement :
        # voir la proposition #21 tracée séparément (_get_current_annee()
        # cassée) — non corrigée ici, juste contournée pour ce test.
        cls.student = cls.env['ensiasd.student'].create({
            'name': 'Étudiant Test API',
            'cne': 'TESTCNEAPI01',
            'filiere_id': cls.filiere.id,
            'annee_inscription': cls.annee.id,
            'annee_courante_id': cls.annee.id,
            'state': 'actif',
        })

    def test_token_field_removed(self):
        """Le champ token en clair ne doit plus exister sur le modèle."""
        self.assertNotIn('token', self.env['ensiasd.api.token']._fields)

    def test_create_token_stores_correct_hash(self):
        """token_hash doit être exactement le SHA-256 du token brut renvoyé, rien d'autre."""
        token_data = self.env['ensiasd.api.token'].create_token(student_id=self.student.id)

        token_record = self.env['ensiasd.api.token'].search([
            ('student_id', '=', self.student.id),
        ], limit=1)

        expected_hash = hashlib.sha256(token_data['token'].encode()).hexdigest()
        self.assertEqual(token_record.token_hash, expected_hash)

    def test_validate_token_still_authenticates(self):
        """validate_token() doit toujours authentifier l'étudiant à partir du token brut renvoyé."""
        token_data = self.env['ensiasd.api.token'].create_token(student_id=self.student.id)

        authenticated_student = self.env['ensiasd.api.token'].validate_token(token_data['token'])

        self.assertEqual(authenticated_student, self.student)

    def test_validate_token_rejects_invalid_token(self):
        """Un token invalide ou inconnu ne doit authentifier personne."""
        self.env['ensiasd.api.token'].create_token(student_id=self.student.id)

        result = self.env['ensiasd.api.token'].validate_token('un-token-qui-nexiste-pas')

        self.assertFalse(result)
