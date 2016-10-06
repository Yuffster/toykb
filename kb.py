"""
Toy Python Knowledgebase
"""

class Knowledgebase():

    def __init__(self):
        self._entities = {}
        self._constraints = {}
        self._inverses = {}
        self._graph = KnowledgeGraph()

    def ent(self, name, type=None):
        """ Adds a new Entity to the graph. """
        self._entities[name] = Entity(self, name, type)

    def get(self, name):
        """ Returns a graph entity. """
        if name not in self._entities:
            raise EntityNotFound(
                "No entity found with name '{}'".format(name)
            )
        return self._entities[name]

    def rel(self, subject, rel, target, certainty=1, scope=None):
        """ Adds a relationship between two objects. """
        scope = scope or self._graph
        if rel in self._inverses:
            # Invert the relationship if necessary
            sub = self.get(target)
            tar = self.get(subject)
            rel = self._inverses[rel]
        else:
            sub = self.get(subject)
            tar = self.get(target)
        constraints = self._get_constraints(rel)
        for c in constraints:
            if c[0] is not None and sub.type != c[0]:
                raise ConstraintException(
                    "Subject of {} must be of type {}; got entity of type"
                    " {} instead"
                    .format(rel, c[0], sub.type)
                )
            if c[1] is not None and tar.type != c[1]:
                raise ConstraintException(
                    "Target of {} must be of type {}; got entity of type "
                    " {} instead"
                    .format(rel, c[1], tar.type)
                )
        scope.add(sub.name, rel, tar.name, certainty)

    def rels(self, subject=None, rel=None, target=None, certainty=None, 
             scope=None):
        """ Returns relationships which meet passed criteria. """
        scope = scope or self._graph
        data = scope.get(subject, rel, target, certainty)
        inverse = self._get_inverse_rels(
            subject, rel, target, certainty, scope
        )
        return join_sets(data, inverse)

    def constrain(self, rel, subject=None, target=None):
        """ Constrains a relationship to types. """
        self._get_constraints(rel).append((subject, target))

    def inverse(self, rel, inverse_of):
        """ Creates an inverse relationship. """
        self._inverses[rel] = inverse_of
        self._inverses[inverse_of] = rel

    def _get_constraints(self, rel):
        if rel not in self._constraints:
            self._constraints[rel] = []
        return self._constraints[rel]

    def _get_inverse_rels(self, subject=None, rel=None, target=None,
                          certainty=None, scope=None):
        if rel not in self._inverses:
            return None
        inverse_rel = self._inverses[rel]
        inverse = scope.get(target, inverse_rel, subject, certainty)
        if inverse is not None:
            data = []
            for i in inverse:
                data.append((i[1], i[0], i[2]))  # Invert relationship.
            return data


class Entity():

    def __init__(self, parent, name, type=None):
        self._type = type
        self._name = name
        self._kb = parent
        self._graph = KnowledgeGraph()
        self._shares = []

    def rel(self, subject=None, rel=None, target=None, certainty=1):
        subject = subject or self.name
        self._kb.rel(subject, rel, target, certainty, self._graph)

    def rels(self, subject=None, rel=None, target=None, certainty=None):
        mine = self._kb.rels(subject, rel, target, certainty, self._graph)
        glob = self._kb.rels(subject, rel, target, certainty)
        return join_sets(mine, glob)

    def local(self, subject=None, rel=None, target=None, certainty=None):
        return self._kb.rels(subject, rel, target, certainty, self._graph)

    def has(self, rel=None, target=None, certainty=None):
        result = self.rels(self.name, rel, target, certainty)
        if len(result) > 0:
            return True
        return False

    def knows(self, subject=None, rel=None, target=None, certainty=1):
        """ This entity is certain this relationship is true. """
        subject = subject or self.name
        if self.rejects(subject, rel, target):
            return False
        if self.certain(subject, rel, target):
            return True
        result = self.rels(subject, rel, target, certainty)
        if len(result) > 0:
            return True
        return False

    def suspects(self, subject=None, rel=None, target=None):
        """ This entity suspects but doesn't know relationship is true. """
        subject = subject or self.name
        return self.knows(subject, rel, target, -1)

    def thinks(self, subject=None, rel=None, target=None):
        """ The entity either suspects or knows the relationship is true. """
        subject = subject or self.name
        return self.knows(subject, rel, target) or \
               self.suspects(subject, rel, target)

    def rejects(self, subject=None, rel=None, target=None):
        """
        Entity won't even entertain a notion within global scope if it knows
        it's false.
        """
        subject = subject or self.name
        rejection = self.local(subject, rel, target, 0)
        if len(rejection) > 0:
            return True

    def certain(self, subject=None, rel=None, target=None):
        """
        Entity won't even entertain a notion within global scope if it knows
        it's true.
        """
        subject = subject or self.name
        sure = self.local(subject, rel, target, 0)
        if len(sure) > 0:
            return True

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name


class KnowledgeGraph():

    """
    The graph stores relationships by key, with a tuple of the subject, the
    target, and the certainty of each relationship.

    Hamlet is located in Elsinore:
        {'located':('hamlet', 'elsinore', 1)}

    Elsinore is the location of Hamlet:
        {'location':('elsinore', 'hamlet', 1)}

    """

    def __init__(self):
        self._rels = {}

    def add(self, subject=None, rel=None, target=None, certainty=1):
        previous = self.get(subject, rel, target)
        if previous: # Don't duplicate.
            for p in previous:
                self._rels[rel].remove(p)
                # Update the certainty.
                self._rels[rel].append((p[0], p[1], certainty))
        else:
            if rel not in self._rels:
                self._rels[rel] = []
            self._rels[rel].append((subject, target, certainty))

    def get(self, subject=None, rel=None, target=None, certainty=None):
        if rel is None or rel not in self._rels:
            return None
        out = []    
        entries = self._rels[rel]
        for i in entries:
            if subject and i[0] != subject:
                continue
            if target and i[1] != target:
                continue
            if certainty is not None and i[2] != certainty:
                continue
            out.append(i)
        if len(out) == 0:
            return None
        return out


def join_sets(*sets):
    o = []
    for s in sets:
        if s is not None:
            o += s
    return o


class ConstraintException(Exception): pass


class EntityNotFound(Exception): pass
