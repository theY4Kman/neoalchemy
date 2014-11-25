import operator
import re

from .. import util, exc
from . import type_api
from .type_api import PropType


NO_ARG = util.symbol('NO_ARG')


class NullType(PropType):
    def literal_processor(self):
        def processor(value):
            return 'NULL'
        return processor


class String(PropType):
    __visit_name__ = 'string'

    def bind_processor(self):
        return str

    def literal_processor(self):
        def processor(value):
            escaped = re.sub('([\'"])', r'\\\1', value)
            return '"' + escaped + '"'
        return processor

    def result_processor(self):
        return str


class Boolean(PropType):
    __visit_name__ = 'boolean'

    def literal_processor(self):
        def processor(value):
            return 'true' if value else 'false'
        return processor


class Integer(PropType):
    def bind_processor(self):
        return int

    def result_processor(self):
        return int


class Float(PropType):
    def bind_processor(self):
        return float

    def result_processor(self):
        return float


class Array(PropType):
    def __init__(self, type_=NO_ARG, *args, **kwargs):
        """Construct an Array type

        If type_ is passed, it is used to transform all values inside the
        array. Any arguments passed to this constructor will be passed to the
        type's constructor.
        """
        if type_ is NO_ARG:
            self.type_ = None
        else:
            self.type_ = type_api.to_instance(type_, *args, **kwargs)

    def bind_processor(self):
        if self.type_ is not None:
            def processor(value):
                impl_processor = self._get_impl_processor('bind_processor')
                return [impl_processor(v) for v in value]
            return processor
        else:
            return list

    def literal_processor(self):
        def processor(value):
            impl_processor = self._get_impl_processor('literal_processor')
            value = [impl_processor(v) for v in value]
            return ''.join(('[', ', '.join(value), ']'))
        return processor

    def result_processor(self):
        if self.type_ is not None:
            def processor(value):
                impl_processor = self._get_impl_processor('result_processor')
                return [impl_processor(v) for v in value]
            return processor
        else:
            return list

    def _get_impl_processor(self, attr):
        getter = operator.attrgetter(attr)
        if self.type_ is None:
            return getter(self.type_)() or (lambda v: v)
        else:
            _cached = {}
            def processor(value):
                type_ = type(value)
                if type_ in _cached:
                    return _cached[type_]
                if type_ not in _type_map:
                    raise exc.UnsupportedCompilationError(
                        'Cannot process %s instances' % type_)
                impl = _type_map[type_]
                impl_processor = getter(impl)() or (lambda v: v)
                _cached[type_] = impl_processor
                return impl_processor
            return processor


BOOLEANTYPE = Boolean()
STRINGTYPE = String()
NULLTYPE = NullType()
INTEGERTYPE = Integer()

_type_map = {
    int: Integer(),
    float: Float(),
    bool: BOOLEANTYPE,
    util.NoneType: NULLTYPE,
}

for type_ in util.string_types:
    _type_map[type_] = String()


type_api.BOOLEANTYPE = BOOLEANTYPE
type_api.STRINGTYPE = STRINGTYPE
type_api.NULLTYPE = NULLTYPE
type_api.INTEGERTYPE = INTEGERTYPE
