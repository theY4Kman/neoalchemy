from neoalchemy import ogm
from neoalchemy.cypher.compiler import Node, Properties, Variable, Relationship, \
    RelType
from neoalchemy.types import *


def basic_test():
    print('Empty')
    print(Node())
    print()

    print('Labeled')
    print(Node('LABEL'))
    print()

    print('Props')
    print(Node(properties=Properties({
        'a': 1,
        'b': 2.0,
        'c': 'see',
        'd': ['coll', 1, 2.0, 'ection'],
    })))
    print()

    print('With anonymous')
    print(Node(variable=Variable(ogm.Node)))
    print()

    print('With anonymous and label')
    print(Node('LABELED', variable=Variable(ogm.Node)))
    print()

    print('With anonymous and label and map')
    print(Node('LABELED', variable=Variable(ogm.Node),
               properties=Properties({'a': '1'})))
    print()

    print('Relationship undirected chain')
    print(Relationship(
        Node(), Node(), Node()
    ))
    print()

    print('Relationship directed chain')
    print(Relationship(
        Node(), RelType.right(), Node(), RelType.right(), Node()
    ))
    print()


if __name__ == '__main__':
    import logging.config
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'formatter': 'message',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            }
        },
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s'
            },
            'message': {
                'format': '%(message)s'
            },
        },
        'loggers': {
            'neoalchemy.ogm.Query': {
                'handlers': ['console'],
                'level': 'DEBUG',
            }
        }
    })

    class Monkey(ogm.Node):
        name = ogm.Prop(String)
        other_name = ogm.Prop('name_number_two', Float)

        def __repr__(self):
            return '(:Monkey {name: %r, other_name: %r})' % (
                self.name, self.other_name)

    r = Monkey.nodes.all()
    print(r)
