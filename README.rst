CypherAlchemy
=============

A SQLAlchemy-like Object Graph Mapper for Neo4j


Example
=======

.. code-block:: python

    from neoalchemy import *

    class Monkey(Node):
        name = Prop(str)

    Query(Monkey).all()
    # or
    Monkey.nodes.all()


Licensing
=========

This library is released under the MIT license. It includes, in no small part,
code from the SQLAlchemy library.
