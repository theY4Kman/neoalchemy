import logging
import os
import requests
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


DOWNLOAD_URL = 'http://neo4j.com/artifact.php?name=neo4j-community-2.1.6-unix.tar.gz'
NEO4J_ROOT = os.path.dirname(__file__)


logger = logging.getLogger(__name__)


def download():
    res = requests.get(DOWNLOAD_URL)
    if res.status_code != 200:
        logger.debug('Response %s when downloading Neo4j from %s: %s',
                     res.status_code, DOWNLOAD_URL, res.content)
        raise Exception('Received {} when downloading Neo4j from {}'.format(
            res.status_code, DOWNLOAD_URL))

    return StringIO(res.content)


def is_installed():
    # TODO
    return False


def install():
    if is_installed():
        logger.info('Neo4j already installed. Not attempting install.')
        return

    fp = download()

