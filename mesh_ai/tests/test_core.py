import unittest
import tempfile
import os
from unittest.mock import patch

class MeshCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        os.environ['GHOST_MESH_HOME'] = self.temp.name
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

    def test_permanent_forget_needs_confirmation(self):
        n = self.core.create_note('Püsiv', 'Kustuta')
        with self.assertRaises(ValueError): self.core.permanently_delete_note(n['id'], 'yes')
        self.assertTrue(self.core.permanently_delete_note(n['id'], 'FORGET'))
        self.assertEqual(self.core.list_notes(True), [])

    def test_rule_requires_explicit_approval(self):
        r = self.core.suggest_rule('Küsi enne kustutamist')
        self.assertEqual(r['status'], 'pending')
        self.assertEqual(self.core.approved_rules(), [])
        self.core.set_rule(r['id'], 'approved')
        self.assertEqual(len(self.core.approved_rules()), 1)

    def test_feedback_creates_lesson_and_simulated_affect(self):
        r = self.core.record_feedback('Alpha', 'Kontrolli arvutust uuesti')
        self.assertGreater(r['frustration_signal'], 0)
        self.assertIn('mitte päris tunne', r['explanation'])
        self.assertTrue(any(n['kind'] == 'lesson' for n in self.core.list_notes()))

    def test_bounds_and_color_validation(self):
        with self.assertRaises(ValueError): self.core.create_note('x', 'y', 'url')
        with self.assertRaises(ValueError): self.core.create_note('x', 'y', 'blue', 99)

    def test_llm_requires_explicit_opt_in(self):
        with patch.object(self.core, '_ollama_chat') as chat:
            result = self.core.think('Tere', use_llm=False)
            chat.assert_not_called()
            self.assertEqual(result['provider'], 'demo-rules')

    def test_llm_never_accepts_remote_url(self):
        with patch.dict(os.environ, {'GHOST_MESH_OLLAMA_URL':'http://example.com:11434','GHOST_MESH_OLLAMA_MODEL':'model'}):
            self.assertIsNone(self.core._ollama_config())

    def test_two_agents_exchange_and_final_synthesis(self):
        with patch.dict(os.environ, {'GHOST_MESH_OLLAMA_URL':'http://127.0.0.1:11434','GHOST_MESH_OLLAMA_MODEL':'test-model'}), \
             patch.object(self.core, '_ollama_chat', side_effect=['alpha draft','beta critique','alpha final']) as chat:
            result = self.core.think('Kuidas testida?', use_llm=True)
        self.assertEqual(chat.call_count, 3)
        self.assertEqual(result['agents']['Beta'], 'beta critique')
        self.assertEqual(result['final'], 'alpha final')
        self.assertEqual(result['provider'], 'ollama-local')

if __name__ == '__main__': unittest.main()
