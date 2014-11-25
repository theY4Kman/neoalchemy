from .. import util
from .compiler import Visitable


# these are back-assigned by cypher_types.
BOOLEANTYPE = None
INTEGERTYPE = None
NULLTYPE = None
STRINGTYPE = None


class PropType(Visitable):
    """Base property type class"""

    def bind_processor(self):
        """Return a function to convert a Python value into a value which can
        be passed as a bindparam.

        If processing is not necessary, return None.

        This is the opposite of result_processor.
        """
        return None

    def result_processor(self):
        """Convert a DB-provided value into its Python equivalent

        If processing is not necessary, return None.

        This is the opposite of bind_processor.
        """
        return None

    def literal_processor(self):
        """Convert a Python value into a literal value which can be placed
        directly into a query.

        If processing is not necessary, return None.
        """
        return None


class PropTypeDecorator(PropType):
    """Allows the creation of types which add additional functionality to an
    existing type.

    This method is preferred to direct subclassing of NeoAlchemy's built-in
    types as it ensures that all required functionality of the underlying type
    is kept in place.
    """

    def __init__(self, *args, **kwargs):
        """Construct a PropTypeDecorator instance.

        Arguments passed here will be passed to the impl constructor.
        """
        if not hasattr(self.__class__, 'impl'):
            raise AssertionError(
                'PropTypeDecorator implementations require a class-level '
                'variable "impl" which refers to the class of type being '
                'decorated')
        self.impl = to_instance(self.__class__.impl, *args, **kwargs)

    def bind_processor(self):
        impl_processor = self.impl.bind_processor()
        if impl_processor is None:
            def processor(value):
                return self.process_bind_param(value)
        else:
            def processor(value):
                return impl_processor(self.process_bind_param(value))
        return processor

    def literal_processor(self):
        impl_processor = self.impl.literal_processor()
        if impl_processor is None:
            def processor(value):
                return self.process_literal(value)
        else:
            def processor(value):
                return impl_processor(self.process_literal(value))
        return processor

    def result_processor(self):
        impl_processor = self.impl.result_processor()
        if impl_processor is None:
            def processor(value):
                return self.process_result(value)
        else:
            def processor(value):
                return impl_processor(self.process_result(value))
        return processor

    def process_bind_param(self, value):
        return value

    def process_literal(self, value):
        return value

    def process_result(self, value):
        return value


def to_instance(typeobj, *arg, **kw):
    if typeobj is None:
        return NULLTYPE

    if util.callable(typeobj):
        return typeobj(*arg, **kw)
    else:
        return typeobj
