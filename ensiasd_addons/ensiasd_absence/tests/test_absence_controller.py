# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged


def _extract_csrf_token(html):
    """Récupère le csrf_token injecté par request.csrf_token() dans un formulaire rendu."""
    anchor = '<input type="hidden" name="csrf_token" value="'
    return html.partition(anchor)[2].partition('"')[0]


@tagged('-at_install', 'post_install')
class TestAbsenceController(HttpCase):
    """
    Tests de non-régression pour les routes publiques du module ensiasd_absence.

    Avant correctif, appel_submit() et justification_submit() levaient un
    KeyError sur request.env['fields'] dès qu'ils tentaient d'écrire
    date_appel / date_justification, ce qui faisait échouer (HTTP 500)
    toute soumission d'appel ou de justification d'absence.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.annee = cls.env['ensiasd.annee'].create({
            'name': 'Année Test 2024-2025',
            'code': 'ATEST2425',
            'date_debut': '2024-09-01',
            'date_fin': '2025-07-31',
            'is_current': True,
            'state': 'open',
        })

        cls.filiere = cls.env['ensiasd.filiere'].create({
            'name': 'Filière Test',
            'code': 'FTEST',
        })

        cls.module = cls.env['ensiasd.module'].create({
            'name': 'Module Test',
            'code': 'MTEST01',
            'filiere_id': cls.filiere.id,
            'semestre': 'S1',
        })

        cls.element = cls.env['ensiasd.element'].create({
            'name': 'Cours Test',
            'module_id': cls.module.id,
            'type_element': 'cm',
        })

        cls.salle = cls.env['ensiasd.salle'].create({
            'name': 'Salle Test',
            'code': 'STEST01',
        })

        cls.groupe = cls.env['ensiasd.groupe'].create({
            'name': 'Groupe Test',
            'code': 'GTEST01',
            'niveau': '1',
            'annee_id': cls.annee.id,
        })

        # annee_inscription / annee_courante_id sont fournis explicitement :
        # _get_current_annee() cherche un enregistrement ensiasd.annee avec
        # state == 'en_cours', une valeur qui n'existe pas dans la Selection
        # du champ state (draft/open/closed) — le default renverrait False.
        cls.student = cls.env['ensiasd.student'].create({
            'name': 'Étudiant Test',
            'cne': 'TESTCNE01',
            'filiere_id': cls.filiere.id,
            'groupe_id': cls.groupe.id,
            'annee_inscription': cls.annee.id,
            'annee_courante_id': cls.annee.id,
            'state': 'actif',
        })

        cls.seance = cls.env['ensiasd.seance'].create({
            'element_id': cls.element.id,
            'date': '2024-10-01',
            'heure_debut': 8.0,
            'heure_fin': 10.0,
            'salle_id': cls.salle.id,
            'groupe_ids': [(6, 0, [cls.groupe.id])],
        })

    def test_appel_submit_sets_date_appel(self):
        """POST /absence/appel/submit ne doit plus lever de KeyError et doit renseigner date_appel."""
        token = self.env['ensiasd.absence.token'].create_token(seance_id=self.seance.id)

        form_page = self.url_open(f'/absence/appel/{token.token}')
        self.assertEqual(form_page.status_code, 200)
        csrf_token = _extract_csrf_token(form_page.text)
        self.assertTrue(csrf_token, "csrf_token introuvable dans le formulaire d'appel rendu")

        response = self.url_open(
            '/absence/appel/submit',
            data={
                'csrf_token': csrf_token,
                'token': token.token,
                f'student_{self.student.id}': 'absent',
            },
        )

        self.assertEqual(response.status_code, 200)

        self.seance.invalidate_recordset()
        self.assertTrue(self.seance.appel_fait)
        self.assertTrue(self.seance.date_appel)
        self.assertEqual(self.seance.state, 'done')

    def test_justification_submit_sets_date_justification(self):
        """POST /absence/justification/submit ne doit plus lever de KeyError et doit renseigner date_justification."""
        absence = self.env['ensiasd.absence'].create({
            'student_id': self.student.id,
            'seance_id': self.seance.id,
        })

        form_page = self.url_open(f'/absence/justification/{absence.id}')
        self.assertEqual(form_page.status_code, 200)
        csrf_token = _extract_csrf_token(form_page.text)
        self.assertTrue(csrf_token, "csrf_token introuvable dans le formulaire de justification rendu")

        response = self.url_open(
            '/absence/justification/submit',
            data={
                'csrf_token': csrf_token,
                'absence_id': absence.id,
                'motif': 'Certificat médical',
            },
        )

        self.assertEqual(response.status_code, 200)

        absence.invalidate_recordset()
        self.assertEqual(absence.state, 'pending')
        self.assertTrue(absence.date_justification)
