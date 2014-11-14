from neoalchemy import ogm
from neoalchemy.compiler import Node, Properties, Variable, Relationship, \
    RelType


def basic_test():
    print 'Empty'
    print Node()
    print

    print 'Labeled'
    print Node('LABEL')
    print

    print 'Props'
    print Node(properties=Properties({
        'a': 1,
        'b': 2.0,
        'c': 'see',
        'd': ['coll', 1, 2.0, 'ection'],
    }))
    print

    print 'With anonymous'
    print Node(variable=Variable(ogm.Node))
    print

    print 'With anonymous and label'
    print Node('LABELED', variable=Variable(ogm.Node))
    print

    print 'With anonymous and label and map'
    print Node('LABELED', variable=Variable(ogm.Node),
               properties=Properties({'a': '1'}))
    print

    print 'Relationship undirected chain'
    print Relationship(
        Node(), Node(), Node()
    )
    print

    print 'Relationship directed chain'
    print Relationship(
        Node(), RelType.right(), Node(), RelType.right(), Node()
    )
    print


if __name__ == '__main__':
    class Monkey(ogm.Node):
        name = ogm.Prop(str)
        other_name = ogm.Prop('name', str)

    r = Monkey.nodes.all()
    print r
