CypherAlchemy
=============

A SQLAlchemy-like Object Graph Mapper for Neo4j


Example
=======

::

    from neoalchemy import *

    class Monkey(Node):
        name = Prop(str)

    Query(Monkey).all()
    # or
    Monkey.nodes.all()
