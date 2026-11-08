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
        import mesh_ai.graph_memory as graph_memory
        self.graph = importlib.reload(graph_memory)

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
            chat.assert_not_called(); self.assertEqual(result['provider'], 'demo-rules')

    def test_llm_never_accepts_remote_url(self):
        with patch.dict(os.environ, {'GHOST_MESH_OLLAMA_URL':'http://example.com:11434','GHOST_MESH_OLLAMA_MODEL':'model'}):
            self.assertIsNone(self.core._ollama_config())

    def test_two_agents_exchange_and_final_synthesis(self):
        with patch.dict(os.environ, {'GHOST_MESH_OLLAMA_URL':'http://127.0.0.1:11434','GHOST_MESH_OLLAMA_MODEL':'test-model'}), \
             patch.object(self.core, '_ollama_chat', side_effect=['alpha draft','beta critique','alpha final']) as chat:
            result = self.core.think('Kuidas testida?', use_llm=True)
        self.assertEqual(chat.call_count, 3); self.assertEqual(result['agents']['Beta'], 'beta critique')
        self.assertEqual(result['final'], 'alpha final'); self.assertEqual(result['provider'], 'ollama-local')

    def test_graph_save_and_coordinator_traversal_is_bounded(self):
        graph = {'title':'Teadmiste kaart','layers':[{'id':'L','name':'Kiht','color':'#123456','opacity':1,'visible':True,'locked':False,'strokes':[]}],
                 'nodes':[{'id':'a','label':'Mesh','description':'lokaalne seadmete võrk','topic':'võrk','x':10,'y':20,'color':'#123456','layer':'L','tags':['mesh']},
                          {'id':'b','label':'Mälu','description':'koordinaator meenutab seoseid','topic':'võrk','x':30,'y':40,'color':'#abcdef','layer':'L','tags':[]},
                          {'id':'c','label':'Reegel','description':'kasutaja kinnitatud piirang','topic':'turve','x':50,'y':60,'color':'#abcdef','layer':'L','tags':[]}],
                 'edges':[{'a':'a','b':'b','relation':'uses'},{'a':'b','b':'c','relation':'governs'}]}
        self.graph.save_graph(graph)
        result=self.graph.coordinate('Mesh',max_depth=2)
        self.assertEqual(len(result['matches']),3)
        self.assertTrue(any(len(p['node_ids'])==3 for p in result['paths']))
        shallow=self.graph.coordinate('Mesh',max_depth=1)
        self.assertLessEqual(len(shallow['matches']),2)

    def test_graph_rejects_bad_edges_and_remote_graph_ids(self):
        with self.assertRaises(ValueError): self.graph.coordinate('x',graph_id='../../other')
        with self.assertRaises(ValueError): self.graph.validate_graph({'title':'x','layers':[],'nodes':[],'edges':[{'a':'no','b':'bad'}]})

if __name__ == '__main__': unittest.main()
