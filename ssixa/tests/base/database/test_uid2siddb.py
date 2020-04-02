from ssixa.base.database.uid2siddb import UidToSidDB
from ssixa.base.database.basedb import SSIXASQLBaseDB

import json
import random
import string

def setup_uid2siddb():
    database_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    with open('db_connection.json', 'r') as f:
        conn = json.loads(f.read())

    source_db = SSIXASQLBaseDB(conn['server'],conn['port'],conn['user'],conn['password'],database_name)
    source_db.connect()
    source_db.initialize()

    db = UidToSidDB(source_db,"instance0")

    assert db is not None
    return db

def test_uid2siddb_setget():
    db = setup_uid2siddb()
    with open('testdata_uid2siddb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[td[s]['uid']] = td[s]['sid']
        # Get items and compare
        for s in td:
            assert db[td[s]['uid']] == [td[s]['sid']]
    finally:
        db.cleanup()
        db._database.erase()

def test_uid2siddb_delete():
    db = setup_uid2siddb()
    with open('testdata_uid2siddb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[td[s]['uid']] = td[s]['sid']
        # Get items and compare
        for s in td:
            del db[td[s]['uid']]
            assert db[td[s]['uid']] == []
    finally:
        db.cleanup()
        db._database.erase()

def test_uid2siddb_values():
    db = setup_uid2siddb()
    with open('testdata_uid2siddb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        sids = []
        # Set items
        for s in td:
            db[td[s]['uid']] = td[s]['sid']
            sids.append(td[s]['sid'])
        # Get items and compare
        assert sids == db.values()
    finally:
        db.cleanup()
        db._database.erase()

def test_uid2siddb_items():
    db = setup_uid2siddb()
    with open('testdata_uid2siddb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        uidssids = []
        # Set items
        for s in td:
            db[td[s]['uid']] = td[s]['sid']
            uidssids.append((td[s]['uid'],td[s]['sid']))
        # Get items and compare
        assert uidssids == db.items()
    finally:
        db.cleanup()
        db._database.erase()