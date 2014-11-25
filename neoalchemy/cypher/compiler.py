import operator
import re

from .. import util
from ..exc import UnsupportedCompilationError, ArgumentError


NO_ARG = util.symbol('NO_ARG')


def _literal_as_text(element):
    if isinstance(element, Element):
        return element
    elif isinstance(element, util.string_types):
        return StringLiteral(element)
    elif isinstance(element, (int, long, float)):
        return Raw(str(element))
    elif hasattr(element, '__iter__'):
        return Collection(element)
    else:
        raise UnsupportedCompilationError(
            'Unsupported literal type %s' % type(element))


class VisitableMeta(type):
    def __init__(cls, clsname, bases, clsdict):
        if clsname != 'Visitable' and hasattr(cls, '__visit_name__'):
            getter = operator.attrgetter('visit_%s' % cls.__visit_name__)

            def _compiler_dispatch(self, visitor, **kwargs):
                try:
                    meth = getter(visitor)
                except AttributeError:
                    raise UnsupportedCompilationError(visitor, cls)
                else:
                    return meth(self, **kwargs)
            cls._compiler_dispatch = _compiler_dispatch

        type.__init__(cls, clsname, bases, clsdict)


class Visitable(object):
    __metaclass__ = VisitableMeta
    __visit_name__ = 'visitable'


class Element(Visitable):
    __visit_name__ = 'element'

    def __str__(self):
        return self._compile()

    @property
    def default_compiler(self):
        return CypherCompiler(None)

    def _compile(self, **kw):
        return self._compiler_dispatch(self.default_compiler, **kw)


class MatchPiece(Element):
    __visit_name__ = 'match_piece'

    def __init__(self, label=None, variable=None, properties=None):
        # Label is static. It's a string or None.
        self.label = label
        self.variable = variable
        self.properties = properties


class Node(MatchPiece):
    __visit_name__ = 'node'


class RelPiece(MatchPiece):
    __visit_name__ = 'rel_piece'


class Match(Element):
    __visit_name__ = 'match'

    def __init__(self, *pieces):
        #: List of MatchPieces
        self.pieces = pieces


class Return(Element):
    __visit_name__ = 'return'

    def __init__(self, *expressions):
        #: List of Expressions to return
        self.expressions = expressions


class Query(Element):
    __visit_name__ = 'query'

    def __init__(self, match=None, return_=None):
        self.match = match
        self.return_ = return_

        if self.match is None or self.return_ is None:
            raise UnsupportedCompilationError(self)


class Relationship(Element):
    __visit_name__ = 'relationship'

    def __init__(self, start_node, *args):
        """Represents a relationship between nodes

        :param start_node: The first node in the relationship. If no other
          arguments are passed, the relationship acts as::

            (start_node)-[]-()

        :param args: Optional number of Node, RelPiece, or RelType objects. If
          multiple Nodes are passed in succession, they're linked as undirected
          relationships, e.g. if you do Relationship(A, B, C), it becomes::

            (A)-[]-(B)-[]-(C)
        """
        if not args:
            raise UnsupportedCompilationError(
                'Relationships must have at least two Nodes')

        self.pieces = []
        last = None
        args = [start_node] + list(args)
        for arg in list(args):
            if isinstance(arg, RelType) and isinstance(last, RelType):
                # Invalid if both reltypes are directed
                if arg.directed and last.directed:
                    raise UnsupportedCompilationError(
                        'Cannot chain two directed reltypes together', self)

                # Cannot point to another reltype
                if arg.left or last.right:
                    raise UnsupportedCompilationError(
                        'Cannot point a reltype to another reltype', self)

            elif not isinstance(arg, (Node, RelPiece, RelType)):
                raise UnsupportedCompilationError(
                    'Relationship args must be RelType, RelPiece, or Node',
                    self)

            self.pieces.append(arg)
            last = arg

        if isinstance(self.pieces[-1], (RelType, RelPiece)):
            raise UnsupportedCompilationError(
                'Relationships must end with a Node')


class RelType(Element):
    __visit_name__ = 'rel_type'

    def __init__(self, left=False, right=False):
        if left and left:
            raise UnsupportedCompilationError(
                'Cannot have both a left and right reltype', self)

        self.left = left
        self.right = right

    @classmethod
    def undirected(cls):
        return cls()

    @classmethod
    def left(cls):
        return cls(left=True)

    @classmethod
    def right(cls):
        return cls(right=True)

    def __eq__(self, other):
        return self.left == other.left and self.right == other.right

    @property
    def directed(self):
        return self.left or self.right


class Expression(Element):
    """An Expression which can be used as a value or returned"""


class Variable(Expression):
    __visit_name__ = 'variable'

    def __init__(self, node_type, name=None):
        """
        :type node_type: neoalchemy.ogm.Node
        """

        #: The OGM Node class this variable represents
        self.node_type = node_type
        #: An optional name of the variable. Should be unique across query.
        self.name = name


class BindParameter(Expression):
    __visit_name__ = 'bindparam'

    def __init__(self, key, value=NO_ARG, type_=None, unique=False):
        """A BindParameter is used as a placeholder in a query. It can carry a
        value to be passed as a parameter, or one can be provided at execution
        time.

        """
        if value is NO_ARG:
            value = None

        # TODO: something about counters and anon maps and yada yada
        self.key = key
        self.value = value
        self.unique = unique


class Properties(Element):
    __visit_name__ = 'properties'

    def __init__(self, props=None, variable=None):
        #: A map of string keys to either literals or Node properties
        self.props = props
        #: A bound variable representing the entire properties map in the query
        self.variable = variable


class StringLiteral(Expression):
    __visit_name__ = 'string'

    def __init__(self, s):
        self.s = s


class Raw(Expression):
    __visit_name__ = 'raw'

    def __init__(self, v):
        self.v = v


class Collection(Expression):
    __visit_name__ = 'collection'

    def __init__(self, elements):
        self.elements = [_literal_as_text(e) for e in elements]


class Compiler(object):
    """Base compiler class"""

    def __init__(self, stmt):
        self.stmt = stmt
        self.string = None

        if self.stmt is not None:
            # Compile our statement, populating any stores a subclass builds
            # (such as variable maps, etc)
            self._compile()

    def _compile(self):
        if self.stmt is None:
            raise ArgumentError('No statement provided to compile')
        self.string = self.stmt._compiler_dispatch(self)
        return self.string

    def compile(self):
        if self.string:
            return self.string
        else:
            return self._compile()


class CypherCompiler(Compiler):
    def __init__(self, stmt):
        #: Maps anonymous Variables (those without a name) to their given name
        self.anon_vars = {}
        #: A counter used to build anonymous Variable names
        self.anon_counter = 1
        #: Maps variable names to their sources
        self.var_names = {}

        super(CypherCompiler, self).__init__(stmt)

    def visit_match_piece(self, match_piece, **kw):
        text = ''
        if match_piece.variable:
            text += match_piece.variable._compiler_dispatch(self, **kw)

        if match_piece.label:
            text += ':' + match_piece.label

        if match_piece.properties:
            # Space out the properties if we have a label or variable
            if match_piece.label or match_piece.variable:
                text += ' '
            text += match_piece.properties._compiler_dispatch(self, **kw)

        return text

    def visit_node(self, node, **kw):
        return '(' + self.visit_match_piece(node, **kw) + ')'

    def visit_rel_piece(self, rel_piece, **kw):
        return '[' + self.visit_match_piece(rel_piece, **kw) + ']'

    def visit_match(self, match, **kw):
        text = 'MATCH '
        pieces = [p._compiler_dispatch(self, **kw) for p in match.pieces]
        text += ', '.join(pieces)
        return text

    def visit_return(self, return_, **kw):
        text = 'RETURN '
        exprs = [e._compiler_dispatch(self, **kw) for e in return_.expressions]
        text += ', '.join(exprs)
        return text

    def visit_query(self, query, **kw):
        text = query.match._compiler_dispatch(self, **kw)
        text += '\n'
        text += query.return_._compiler_dispatch(self, **kw)
        return text

    def visit_variable(self, variable, **kw):
        name = variable.name
        if name is None:
            key = variable.node_type._impl.key
            if key not in self.anon_vars:
                self.anon_vars[key] = 'anon_' + str(self.anon_counter)
                self.anon_counter += 1
            name = self.anon_vars[key]
            variable.name = name

        # keep track of variable names
        if name not in self.var_names:
            self.var_names[name] = variable

        return name

    def visit_bindparam(self, bindparam, **kw):
        # TODO
        raise NotImplementedError

    def visit_properties(self, properties, **kw):
        text = '{'

        if properties.variable:
            text += properties.variable._compiler_dispatch(self, **kw)

        if properties.props:
            props = []
            for key, value in list(properties.props.items()):
                if not isinstance(key, util.string_types):
                    raise UnsupportedCompilationError(
                        'Properties keys must be strings', self, properties)
                prop = key + ': '
                value = _literal_as_text(value)
                prop += value._compiler_dispatch(self, **kw)
                props.append(prop)
            text += ', '.join(props)

        text += '}'
        return text

    def visit_relationship(self, relationship, **kw):
        text = ''
        last = None
        for piece in relationship.pieces:
            if isinstance(piece, Node) and isinstance(last, Node):
                text += RelType.undirected()._compiler_dispatch(self, **kw)
            text += piece._compiler_dispatch(self, **kw)
            last = piece
        return text

    def visit_rel_type(self, rel_type, **kw):
        if rel_type.left:
            return '<-'
        elif rel_type.right:
            return '->'
        else:
            return '-'

    def visit_string(self, string, **kw):
        escaped = re.sub('([\'"])', r'\\\1', string.s)
        return '"' + escaped + '"'

    def visit_raw(self, raw, **kw):
        return raw.v

    def visit_collection(self, collection, **kw):
        text = '['
        elements = [e._compiler_dispatch(self, **kw)
                    for e in collection.elements]
        text += ', '.join(elements)
        text += ']'
        return text
