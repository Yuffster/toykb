import unittest
import kb


class KnowlegeTest(unittest.TestCase):

    def setUp(self):
        self.kb = kb.Knowledgebase()

    def test_basic_knowledge_graph(self):
        graph = kb.KnowledgeGraph()
        graph.add('claudius', 'kill', 'khamlet')
        entry = ('claudius', 'khamlet', 1)
        self.assertEqual(graph._rels, {'kill':[entry]})
        self.assertEqual(graph.get(subject='claudius', rel='kill'), [entry])
        self.assertEqual(graph.get(target='khamlet', rel='kill'), [entry])
        self.assertEqual(graph.get(subject='khamlet', rel='kill'), None)
        self.assertEqual(graph.get(target='claudius', rel='kill'), None)

    def test_entity_not_found(self):
        with self.assertRaises(kb.EntityNotFound):
            self.kb.rel('foo', 'bar', 'bizz')
        self.kb.ent('foo')
        with self.assertRaises(kb.EntityNotFound):
            self.kb.rel('foo', 'bar', 'bizz')
        self.kb.ent('bizz')
        self.kb.rel('foo', 'bar', 'bizz')

    def test_define_constrained_relationship(self):
        e = self.kb.ent('elsinore', type='place')
        h = self.kb.ent('hamlet', type='person')
        self.kb.constrain('located', subject='person', target='place')
        with self.assertRaises(kb.ConstraintException):
            self.kb.rel('elsinore', 'located', 'hamlet')
        self.kb.rel('hamlet', 'located', 'elsinore')
        h_locs = self.kb.rels('hamlet', 'located', 'elsinore')
        self.assertEqual([('hamlet', 'elsinore', 1)], h_locs)
        result = self.kb.get('hamlet').has('located', 'elsinore')
        self.assertEqual(result, True)

    def test_inverse_relationship(self):
        self.kb.ent('elsinore', type='place')
        self.kb.ent('hamlet', type='person')
        self.kb.inverse('location', 'located')
        self.kb.rel('elsinore', 'location', 'hamlet')
        expected = {'located': [('hamlet', 'elsinore', 1)]}
        self.assertEqual(self.kb._graph._rels, expected)
        result = self.kb.get('hamlet').has('located', 'elsinore')
        self.assertEqual(result, True)
        result = self.kb.get('elsinore').has('location', 'hamlet')
        self.assertEqual(result, True)

    def test_inverse_relationship_constraints(self):
        self.kb.ent('elsinore', type='place')
        self.kb.ent('hamlet', type='person')
        self.kb.constrain('located', subject='person', target='place')
        self.kb.inverse('location', 'located')
        with self.assertRaises(kb.ConstraintException):
            self.kb.rel('elsinore', 'location', 'elsinore')

    def test_search_inverse_relationships(self):
        self.kb.ent('elsinore', type='place')
        self.kb.ent('hamlet', type='person')
        self.kb.inverse('location', 'located')
        self.kb.rel('elsinore', 'location', 'hamlet')
        e1 = ('elsinore', 'hamlet', 1)
        e2 = ('hamlet', 'elsinore', 1)
        result = self.kb.get('elsinore').rels(rel='location')
        self.assertEqual(result, [e1])
        result = self.kb.get('hamlet').rels(rel='located')
        self.assertEqual(result, [e2])
        
    def test_post_inverse_relationship(self):
        self.kb.ent('elsinore', type='place')
        self.kb.ent('hamlet', type='person')
        self.kb.rel('elsinore', 'location', 'hamlet')
        expected = {'location': [('elsinore', 'hamlet', 1)]}
        self.assertEqual(expected, self.kb._graph._rels)
        self.kb.inverse('location', 'located')
        h = self.kb.get('hamlet')
        e = self.kb.get('elsinore')
        self.assertEqual(True, h.has('located', 'elsinore'))
        self.assertEqual(True, e.has('location', 'hamlet'))

    def test_search_post_inverse_relationships(self):
        self.kb.ent('elsinore', type='place')
        self.kb.ent('hamlet', type='person')
        self.kb.rel('elsinore', 'location', 'hamlet')
        self.kb.inverse('location', 'located')
        e1 = ('elsinore', 'hamlet', 1)
        e2 = ('hamlet', 'elsinore', 1)
        result = self.kb.get('elsinore').rels(rel='location')
        self.assertEqual(result, [e1])
        result = self.kb.get('hamlet').rels(rel='located')
        self.assertEqual(result, [e2])

    def test_all_relationships(self):
        self.kb.ent('elsinore')
        self.kb.ent('paris')
        self.kb.ent('hamlet')
        self.kb.ent('laertes')
        self.kb.rel('elsinore', 'location', 'hamlet')
        self.kb.rel('laertes', 'located', 'paris')
        self.kb.inverse('location', 'located')
        result = self.kb.rels(rel='location')
        expected = [('elsinore', 'hamlet', 1), ('paris', 'laertes', 1)]
        self.assertEqual(expected, result)

    def test_knowledge_scoping(self):
        self.kb.ent('khamlet')
        self.kb.ent('claudius')
        self.kb.ent('hamlet')
        c = self.kb.get('claudius')
        h = self.kb.get('hamlet')
        # Claudius secretly kills King Hamlet.
        c.rel(rel='kills', target='khamlet')
        # Claudius knows he killed King Hamlet.
        self.assertEqual(True, c.knows('claudius', 'kills', 'khamlet'))
        # Complete list of people killed by Claudius.
        result = c.rels(rel='kills')
        self.assertEqual([('claudius', 'khamlet', 1)], result)
        # Hamlet does not know.
        self.assertEqual(False, h.knows('claudius', 'kills', 'khamlet'))
        # He doesn't even suspect it.
        self.assertEqual(False, h.suspects('claudius', 'kills', 'khamlet'))
        # A ghost shows up, weird.  Certainty is -1; needs to be verified.
        h.rel('claudius', 'kills', 'khamlet', certainty=-1)
        # He still doesn't KNOW Claudius killed his father.
        self.assertEqual(False, h.knows('claudius', 'kills', 'khamlet'))
        # But he SUSPECTS it.
        self.assertEqual(True, h.thinks('claudius', 'kills', 'khamlet'))
        self.assertEqual(True, h.suspects('claudius', 'kills', 'khamlet'))
        # Then there's a play or something.
        h.rel('claudius', 'kills', 'khamlet', certainty=1)
        # Hamlet both knows and thinks Claudius killed his father.
        self.assertEqual(True, h.knows('claudius', 'kills', 'khamlet'))
        self.assertEqual(True, h.thinks('claudius', 'kills', 'khamlet'))
        # He no longer SUSPECTS, since his certainty has been upgraded.
        self.assertEqual(False, h.suspects('claudius', 'kills', 'khamlet'))

    def test_knowledge_rejection(self):
        self.kb.ent('khamlet')
        self.kb.ent('claudius')
        self.kb.ent('gertrude')
        self.kb.ent('hamlet')
        c = self.kb.get('claudius')
        g = self.kb.get('gertrude')
        h = self.kb.get('hamlet')
        # Claudius kills King Hamlet in broad daylight and everyone knows.
        self.kb.rel('claudius', 'kills', 'khamlet', 1)
        # Except Gertrude, she KNOWS her new husband would never.
        g.rel('claudius', 'kills', 'khamlet', 0)
        self.assertEqual(True, h.knows('claudius', 'kills', 'khamlet'))
        self.assertEqual(False, g.knows('claudius', 'kills', 'khamlet'))
