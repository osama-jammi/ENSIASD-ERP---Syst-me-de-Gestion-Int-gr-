# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStudentAutoInscribeBehavior(TransactionCase):
    """
    Non-régression fonctionnelle pour le correctif du N+1 dans
    _auto_inscribe_modules() et action_inscribe_next_year() : le passage à
    une recherche groupée des inscriptions existantes ne doit rien changer
    au nombre ni à l'identité des inscriptions créées, ni casser
    l'idempotence (rappeler la logique ne doit jamais créer de doublon).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.annee = cls.env['ensiasd.annee'].create({
            'name': 'Année Test 2024-2025',
            'code': 'ATEST2425-INSC',
            'date_debut': '2024-09-01',
            'date_fin': '2025-07-31',
            'is_current': True,
            'state': 'open',
        })

        cls.filiere = cls.env['ensiasd.filiere'].create({
            'name': 'Filière Test Inscription',
            'code': 'FTESTINSC',
        })

        cls.module_s1 = cls.env['ensiasd.module'].create({
            'name': 'Module S1 Test',
            'code': 'MS1TEST',
            'filiere_id': cls.filiere.id,
            'semestre': 'S1',
        })
        cls.module_s2 = cls.env['ensiasd.module'].create({
            'name': 'Module S2 Test',
            'code': 'MS2TEST',
            'filiere_id': cls.filiere.id,
            'semestre': 'S2',
        })
        cls.module_s3 = cls.env['ensiasd.module'].create({
            'name': 'Module S3 Test',
            'code': 'MS3TEST',
            'filiere_id': cls.filiere.id,
            'semestre': 'S3',
        })
        cls.module_s4 = cls.env['ensiasd.module'].create({
            'name': 'Module S4 Test',
            'code': 'MS4TEST',
            'filiere_id': cls.filiere.id,
            'semestre': 'S4',
        })

    def _create_student(self, cne):
        return self.env['ensiasd.student'].create({
            'name': f'Étudiant Test {cne}',
            'cne': cne,
            'filiere_id': self.filiere.id,
            'niveau': '1',
            'annee_inscription': self.annee.id,
            'annee_courante_id': self.annee.id,
            'state': 'actif',
        })

    def test_auto_inscribe_modules_creates_one_inscription_per_module(self):
        """create() (niveau 1) doit inscrire l'étudiant à S1 et S2, une fois chacun."""
        student = self._create_student('TESTCNEINSC01')

        inscriptions = self.env['ensiasd.inscription'].search([('student_id', '=', student.id)])
        self.assertEqual(len(inscriptions), 2)
        self.assertEqual(
            set(inscriptions.mapped('module_id.id')),
            {self.module_s1.id, self.module_s2.id},
        )

    def test_auto_inscribe_modules_is_idempotent(self):
        """Rappeler _auto_inscribe_modules() sur un étudiant déjà inscrit ne doit créer aucun doublon."""
        student = self._create_student('TESTCNEINSC02')
        self.assertEqual(
            len(self.env['ensiasd.inscription'].search([('student_id', '=', student.id)])), 2
        )

        student._auto_inscribe_modules()

        self.assertEqual(
            len(self.env['ensiasd.inscription'].search([('student_id', '=', student.id)])), 2
        )

    def test_inscribe_next_year_skips_already_existing_inscriptions(self):
        """
        Si une inscription cible existe déjà (ex. saisie manuelle antérieure),
        action_inscribe_next_year() ne doit pas la dupliquer, seulement
        compléter les modules manquants.
        """
        student = self._create_student('TESTCNEINSC03')

        # Simuler une inscription S3 déjà existante avant l'appel à l'action.
        existing_inscription = self.env['ensiasd.inscription'].create({
            'student_id': student.id,
            'module_id': self.module_s3.id,
            'annee_id': self.annee.id,
            'state': 'confirmed',
        })

        student.action_inscribe_next_year()

        self.assertEqual(student.niveau, '2')

        inscriptions_s3_s4 = self.env['ensiasd.inscription'].search([
            ('student_id', '=', student.id),
            ('module_id', 'in', [self.module_s3.id, self.module_s4.id]),
        ])
        # Pas de doublon pour S3 (déjà existant), une seule nouvelle inscription pour S4.
        self.assertEqual(len(inscriptions_s3_s4), 2)
        self.assertIn(existing_inscription, inscriptions_s3_s4)


@tagged('post_install', '-at_install')
class TestStudentAutoInscribeQueryCount(TransactionCase):
    """
    Test isolé, séparé des tests comportementaux ci-dessus : si ce test
    échoue (comptage de requêtes), cela ne doit pas masquer un échec de
    non-régression fonctionnelle, et inversement.

    On ne fige pas de nombre absolu de requêtes (fragile, dépendant de la
    version d'Odoo) : on compare le coût d'un appel à _auto_inscribe_modules()
    quand tous les modules sont déjà inscrits (donc aucune création, seule la
    vérification d'existence est exercée) entre 1 module et 5 modules. Avant
    le correctif, chaque module ajouté ajoutait une requête ; après, le
    surcoût doit rester marginal et indépendant du nombre de modules.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.annee = cls.env['ensiasd.annee'].create({
            'name': 'Année Test QueryCount',
            'code': 'ATEST-QC',
            'date_debut': '2024-09-01',
            'date_fin': '2025-07-31',
            'is_current': True,
            'state': 'open',
        })

    def _make_filiere_with_modules(self, code_prefix, nb_modules):
        filiere = self.env['ensiasd.filiere'].create({
            'name': f'Filière {code_prefix}',
            'code': code_prefix,
        })
        modules = self.env['ensiasd.module']
        for i in range(nb_modules):
            modules |= self.env['ensiasd.module'].create({
                'name': f'Module {code_prefix}{i}',
                'code': f'{code_prefix}{i}',
                'filiere_id': filiere.id,
                'semestre': 'S1',
            })
        return filiere, modules

    def test_existing_check_query_count_does_not_scale_with_module_count(self):
        filiere_1, modules_1 = self._make_filiere_with_modules('QC1', 1)
        filiere_5, modules_5 = self._make_filiere_with_modules('QC5', 5)

        student_1 = self.env['ensiasd.student'].create({
            'name': 'Étudiant QueryCount 1',
            'cne': 'TESTCNEQC01',
            'filiere_id': filiere_1.id,
            'niveau': '1',
            'annee_inscription': self.annee.id,
            'annee_courante_id': self.annee.id,
            'state': 'actif',
        })
        student_5 = self.env['ensiasd.student'].create({
            'name': 'Étudiant QueryCount 5',
            'cne': 'TESTCNEQC02',
            'filiere_id': filiere_5.id,
            'niveau': '1',
            'annee_inscription': self.annee.id,
            'annee_courante_id': self.annee.id,
            'state': 'actif',
        })

        # Les deux étudiants sont déjà inscrits à tous leurs modules (via
        # create()) : les appels ci-dessous n'exercent que la vérification
        # d'existence, aucune création n'a lieu.
        self.env.flush_all()

        count0 = self.env.cr.sql_log_count
        student_1._auto_inscribe_modules()
        self.env.flush_all()
        count_for_1_module = self.env.cr.sql_log_count - count0

        count0 = self.env.cr.sql_log_count
        student_5._auto_inscribe_modules()
        self.env.flush_all()
        count_for_5_modules = self.env.cr.sql_log_count - count0

        delta = count_for_5_modules - count_for_1_module
        self.assertLessEqual(
            delta, 2,
            f"Le nombre de requêtes augmente avec le nombre de modules "
            f"({count_for_1_module} requêtes pour 1 module, "
            f"{count_for_5_modules} pour 5 modules, delta={delta}) : "
            f"la vérification des inscriptions existantes semble de nouveau "
            f"faire une requête par module."
        )
