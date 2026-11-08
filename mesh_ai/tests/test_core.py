import unittest
import tempfile
from pathlib import Path
import os

class MeshCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        os.environ['GHOST_MESH_HOME'] = self.temp.name
        # Import after selecting an isolated data directory.
        import importlib
        import mesh_ai.core as core
        self.core = importlib.reload(core)

    def tearDown(self): self.temp.cleanup()

    def test_create_and_retrieve_note(self):
        n = self.core.create_note('Värvid', 'Mesh mälu', 'violet', 20, 4, ['AI'])
        self.assertEqual(self.core.list_notes()[0]['id'], n['id'])
        self.assertTrue(self.core.retrieve_memory('Mesh mälu'))

    def test_forget_archives_not_deletes(self):
        n = self.core.create_note('Arhiiv', 'Salvesta ära')
        self.assertTrue(self.core.forget_note(n['id']))
        self.assertEqual(self.core.list_notes(), [])
        self.assertTrue(self.core.list_notes(True))

    def test_rule_requires_explicit_approval(self):
        r = self.core.suggest_rule('Küsi enne kustutamist')
        self.assertEqual(r['status'], 'pending')
        self.assertEqual(self.core.approved_rules(), [])
        self.core.set_rule(r['id'], 'approved')
        self.assertEqual(len(self.core.approved_rules()), 1)

    def test_feedback_creates_lesson_and_signal(self):
        r = self.core.record_feedback('Alpha', 'Kontrolli arvutust uuesti')
        self.assertGreater(r['frustration_signal'], 0)
        self.assertTrue(any(n['kind'] == 'lesson' for n in self.core.list_notes()))

    def test_bounds_and_color_validation(self):
        with self.assertRaises(ValueError): self.core.create_note('x', 'y', 'url')
        with self.assertRaises(ValueError): self.core.create_note('x', 'y', 'blue', 99)

if __name__ == '__main__': unittest.main()
