This directory houses the Neo4j test instance. The tests will ask to download Neo4j community edition if it's not found in this directory. Before each test session, the configuration files will be overridden to set the correct ports for the REST interface (and to ensure any unnecessary features are disabled).

Neo4j will be (re)started before every test session, and ended upon completion.
