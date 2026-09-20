# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStudentApiPasswordDisclosure(TransactionCase):
    """
    Non-régression : ni action_regenerate_api_password() ni
    action_show_api_credentials() ne doivent renvoyer le mot de passe API
    en clair dans leur notification.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.annee = cls.env['ensiasd.annee'].create({
            'name': 'Année Test 2024-2025',
            'code': 'ATEST2425-PWD',
            'date_debut': '2024-09-01',
            'date_fin': '2025-07-31',
            'is_current': True,
            'state': 'open',
        })

        cls.filiere = cls.env['ensiasd.filiere'].create({
            'name': 'Filière Test PWD',
            'code': 'FTESTPWD',
        })

        # CNE + CIN fournis : le create() de student_api_mixin génère
        # automatiquement un mot de passe API (CNE+CIN) à la création.
        cls.student = cls.env['ensiasd.student'].create({
            'name': 'Étudiant Test PWD',
            'cne': 'TESTCNEPWD01',
            'cin': 'TESTCINPWD01',
            'filiere_id': cls.filiere.id,
            'annee_inscription': cls.annee.id,
            'annee_courante_id': cls.annee.id,
            'state': 'actif',
        })

    def _expected_password(self):
        return f"{self.student.cne}+{self.student.cin}"

    def test_regenerate_password_does_not_leak_plaintext(self):
        """La notification de régénération ne doit pas contenir le mot de passe."""
        result = self.student.action_regenerate_api_password()

        message = result['params']['message']
        self.assertNotIn(self._expected_password(), message)
        # Le mot de passe doit malgré tout être fonctionnel après régénération.
        self.assertTrue(self.student.check_api_password(self._expected_password()))

    def test_show_credentials_does_not_leak_plaintext(self):
        """La notification de statut ne doit pas contenir le mot de passe."""
        result = self.student.action_show_api_credentials()

        message = result['params']['message']
        self.assertNotIn(self._expected_password(), message)
        # Elle doit rester utile pour le support : CNE et statut visibles.
        self.assertIn(self.student.cne, message)
