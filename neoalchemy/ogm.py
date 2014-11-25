# FIXME: Stopgap measure to get a neo4j DB quickly
from py2neo import neo4j
db = neo4j.GraphDatabaseService('http://localhost:7474/db/data/')

import logging
import operator

from . import util, exc
from .cypher import compiler, type_api


NA_STATE_INSTANCE_VAR = '_neo_state'
NA_NODE_INFO_INSTANCE_VAR = '_node_info'

_instance_state = operator.attrgetter(NA_STATE_INSTANCE_VAR)
_instance_info = operator.attrgetter(NA_NODE_INFO_INSTANCE_VAR)


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

        comp = compiler.CypherCompiler(query_node)
        query_string = comp.compile()
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


class NodeInfo(object):
    """Stores metadata about a Node"""

    def __init__(self, node_type):
        self.node_type = node_type
        self.properties = {}

    def add_property(self, prop):
        prop._set_parent(self.node_type)
        self.properties[prop.key] = prop

    def remove_property(self, prop):
        del self.properties[prop.key]

    @property
    def result_processors(self):
        """A mapping of prop keys to their result_processors.
        """
        callables = {}
        for key, prop in list(self.properties.items()):
            callables[key] = prop.result_processor
        return callables


class NodeMeta(type):
    def __init__(cls, clsname, bases, clsdict):
        if (clsname != 'NodeMeta' and hasattr(cls, '__label__') and
                    clsname != 'Node'):
            if cls.__label__ is None and bases != (object,):
                cls.__label__ = clsname

            setattr(cls, NA_STATE_INSTANCE_VAR, {})

            info = NodeInfo(cls)
            setattr(cls, NA_NODE_INFO_INSTANCE_VAR, info)

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
                    info.add_property(attr)

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

        self.type_ = type_api.to_instance(type_)
        self.name = name
        self.key = kwargs.pop('key', name)

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
        state = _instance_state(instance)
        state[self.name] = value

    @property
    def result_processor(self):
        """Return the result_processor for this prop's type. If the type does
        not need a result_processor, a callable returning its single argument
        will be returned, so this property can always be used as a callable.
        """
        processor = self.type_.result_processor()
        if processor is None:
            processor = lambda v: v
        return processor


class NodeImpl(object):
    """Handles various operations for Nodes"""

    def __init__(self, node_type):
        self.node_type = node_type

    def inflate(self, node):
        """Given a result from the database, return a Node which represents it
        """
        instance = self.node_type()
        # XXX: assumes it's a neo4j.Node
        props = node.get_properties()
        _info = _instance_info(instance)
        _processors = _info.result_processors
        for key, value in list(props.items()):
            if key in _processors:
                props[key] = _processors[key](value)
        instance._state = props
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
