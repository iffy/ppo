# Copyright (c) The ppo team
# See LICENSE for details.

import tempfile
import os

from ppo import plugins

from structlog import get_logger

try:
    from pysqlite2 import dbapi2 as sqlite
except ImportError:
    import sqlite3 as sqlite


class SQLite3Parser(plugins.ParserPlugin):
    """
    I parse SQLite databases (the raw database,
        not the output of queries)
    """

    name = 'sqlite-db'

    def readProbability(self, instream):
        firstpart = instream.read(20)
        if firstpart.startswith('SQLite format 3\x00'):
            return 60
        else:
            return 0

    def parse(self, instream):
        # XXX it would be nice to not have to write to a temporary file :(
        log = get_logger()
        log = log.bind(plugin=self.name)

        tempdir = tempfile.mkdtemp()
        tmpdb = os.path.join(tempdir, 'db.sqlite')
        result = {'tables': {}}
        try:
            with open(tmpdb, 'wb') as fh:
                log.msg('Copying data to temp file', filename=tmpdb)
                fh.write(instream.read())
            db = sqlite.connect(tmpdb)
            db.row_factory = sqlite.Row
            log.msg('Connected to db', filename=tmpdb)

            r = db.execute(
                "select tbl_name "
                "from sqlite_master "
                "where type='table'")
            tables = [x[0] for x in r.fetchall()]
            log.msg('Found these tables', tables=tables)
            for table in tables:
                l = log.bind(table=table)
                r = db.execute(
                    "select * from %s" % (table,))
                l.msg('Found rows', rowcount=r.rowcount)
                data = [dict(x) for x in r.fetchall()]
                result['tables'][table] = data
            db.close()
            return result
        except:
            raise
        finally:
            try:
                os.remove(tmpdb)
                log.msg('Removed temporary file', filename=tmpdb)
            except:
                log.msg('Error removing temporary file', filename=tmpdb, exc_info=True)
            try:
                os.rmdir(tempdir)
                log.msg('Removed temporary dir', directory=tempdir)
            except:
                log.msg('Error removing temporary dir', directory=tempdir, exc_info=True)

