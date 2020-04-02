from ssixa.base.database.ssixadb import StatisticsLoggerDB
from ssixa.base.database.basedb import SSIXASQLBaseDB
from ssixa.base.database.basedbobject import BaseStatistic

import json
import random
import string


def setup_statisticsloggerdb():
    database_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    with open('db_connection.json', 'r') as f:
        conn = json.loads(f.read())

    source_db = SSIXASQLBaseDB(conn['server'],conn['port'],conn['user'],conn['password'],database_name)
    source_db.connect()
    source_db.initialize()

    db = StatisticsLoggerDB(source_db)

    assert db is not None
    return db

def test_statisloggerdb_logandretrieve():
    db = setup_statisticsloggerdb()
    with open('testdata_ssixadb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    statistics = td['statistics']
    try:
        # Set items
        for s in statistics:
            db.log(statistics[s]['name'],statistics[s]['value'],statistics[s]['application'])
            logdata = db.get_logs(statistics[s]['name'])
            assert statistics[s]['name'] == logdata[0].name
            assert statistics[s]['value'] == logdata[0].value
            assert statistics[s]['application'] == logdata[0].application
    finally:
        db.cleanup()
        db._database.erase()