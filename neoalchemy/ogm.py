# FIXME: Stopgap measure to get a neo4j DB quickly
from py2neo import neo4j
db = neo4j.GraphDatabaseService('http://localhost:7474/db/data/')

import logging

from . import compiler, util, exc


class Query(object):
    """Keeps track of """

    logger = logging.getLogger(__name__ + '.Query')

    def __init__(self, *entities):
        #: The entities which will be returned by the query
        self.entities = entities

    def all(self):
        return list(self)

    def __iter__(self):
        return iter(self._execute())

    def _execute(self):
        match_pieces = []
        return_pieces = []
        for entity in self.entities:
            variable = compiler.Variable(entity)
            match_pieces.append(
                compiler.Node(label=entity.__label__, variable=variable))
            return_pieces.append(variable)

        match = compiler.Match(*match_pieces)
        return_ = compiler.Return(*return_pieces)
        query_node = compiler.Query(match=match, return_=return_)

        comp = compiler.CypherCompiler()
        query_string = query_node._compiler_dispatch(comp)
        self.logger.debug(query_string)
        query = neo4j.CypherQuery(db, query_string)

        results = query.execute()
        inflated = []
        for record in results.data:
            # XXX: assuming only one column per record. prob not always true
            column, value = record.columns[0], record.values[0]
            node_type = comp.var_names[column].node_type
            impl = node_type._impl
            inflated.append(impl.inflate(value))

        return inflated


class NodeManager(object):
    """Handles creation of query from simple methods"""

    query_class = Query

    def __init__(self, node_type=None):
        #: The source Node class
        self.node_type = node_type

    def _set_node_type(self, node_type):
        self.node_type = node_type

    def get_query(self):
        return self.query_class(self.node_type)

    def all(self):
        return self.get_query().all()


class NodeMeta(type):
    def __init__(cls, clsname, bases, clsdict):
        if (clsname != 'NodeMeta' and hasattr(cls, '__label__') and
                    clsname != 'Node'):
            if cls.__label__ is None and bases != (object,):
                cls.__label__ = clsname

            #: Underlying state of data.
            cls._state = {}
            #: Records all the properties for iteration
            cls.__properties__ = set()

            # Allow Node subclasses to override implementations
            if not hasattr(cls, '_impl'):
                cls._impl = NodeImpl(cls)

            for name in dir(cls):
                attr = getattr(cls, name)
                if isinstance(attr, type) and issubclass(attr, NodeManager):
                    attr = attr(cls)
                    setattr(cls, name, attr)
                elif isinstance(attr, NodeManager):
                    attr._set_node_type(cls)
                elif isinstance(attr, Prop):
                    if attr.name is None:
                        attr.name = name
                    attr._set_parent(cls)
                    cls.__properties__.add(attr)

        type.__init__(cls, clsname, bases, clsdict)


class Prop(object):
    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        type_ = kwargs.pop('type_', None)
        args = list(args)
        if args:
            if isinstance(args[0], util.string_types):
                if name is not None:
                    raise exc.ArgumentError(
                        "May not pass name positionally and as a keyword.")
                name = args.pop(0)
        if args:
            if type_ is not None:
                raise exc.ArgumentError(
                    "May not pass type_ positionally and as a keyword.")
            type_ = args.pop(0)

        if args or kwargs:
            raise exc.ArgumentError('Unhandled arguments', args, kwargs)

        self.type_ = type_
        self.name = name

        self.parent = None

    def _set_name(self, name):
        self.name = name

    def _set_parent(self, parent):
        self.parent = parent

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return instance._state.get(self.name)

    def __set__(self, instance, value):
        if instance is None:
            # XXX: does this happen?
            assert 0, 'wut?'
        else:
            instance._state[self.name] = value


class NodeImpl(object):
    """Handles various operations for Nodes"""

    def __init__(self, node_type):
        self.node_type = node_type

    def inflate(self, node):
        """Given a result from the database, return a Node which represents it
        """
        instance = self.node_type()
        # XXX: assumes it's a neo4j.Node
        # TODO: unpacking with type support
        instance._state = node.get_properties()
        return instance

    @property
    def key(self):
        return self.node_type.__module__ + '.' + self.node_type.__name__


class BaseNode(object):
    __metaclass__ = NodeMeta
    nodes = NodeManager


class Node(BaseNode):
    """Base class for OGM Nodes"""
    __label__ = None
