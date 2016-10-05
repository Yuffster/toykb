import unittest
import kb


class DocumentTest(unittest.TestCase):

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
		self.assertEqual(self.kb.get('hamlet').has('located', 'elsinore'), True)

	def test_inverse_relationship(self):
		self.kb.ent('elsinore', type='place')
		self.kb.ent('hamlet', type='person')
		self.kb.inverse('location', 'located')
		self.kb.rel('elsinore', 'location', 'hamlet')
		self.assertEqual(self.kb._graph._rels, {'located': [('hamlet', 'elsinore', 1)]})
		self.assertEqual(self.kb.get('hamlet').has('located', 'elsinore'), True)
		self.assertEqual(True, self.kb.get('elsinore').has('location', 'hamlet'))

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
		self.assertEqual(self.kb._graph._rels, {'location': [('elsinore', 'hamlet', 1)]})
		self.kb.inverse('location', 'located')
		self.assertEqual(True, self.kb.get('hamlet').has('located', 'elsinore'))
		self.assertEqual(True, self.kb.get('elsinore').has('location', 'hamlet'))

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
		self.assertEqual(result, [('elsinore', 'hamlet', 1), ('paris', 'laertes', 1)])
