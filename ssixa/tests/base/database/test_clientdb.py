from ssixa.base.database.clientdb import ClientDB
from ssixa.base.database.basedb import SSIXASQLBaseDB

import json
import random
import string


def setup_clientdb():
    database_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    with open('db_connection.json', 'r') as f:
        conn = json.loads(f.read())

    source_db = SSIXASQLBaseDB(conn['server'],conn['port'],conn['user'],conn['password'],database_name)
    source_db.connect()
    source_db.initialize()

    db = ClientDB(source_db)

    assert db is not None
    return db

def test_clientdb_setget():
    db = setup_clientdb()
    with open('testdata_clientdb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[s] = td[s]
        # Get items and compare
        for s in td:
            assert td[s] == db[s]
        # Get items and compare - second method
        for s in td:
            assert td[s] == db.get(s)
    finally:
        db.cleanup()
        db._database.erase()

def test_clientdb_contains():
    db = setup_clientdb()
    with open('testdata_clientdb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[s] = td[s]
        # Contains
        for s in td:
            assert s in db
    finally:
        db.cleanup()
        db._database.erase()

def test_clientdb_keys():
    db = setup_clientdb()
    with open('testdata_clientdb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[s] = td[s]
        # Keys
        k = db.keys()
        for s in td:
            if s in k:
                assert True
            else:
                assert False
    finally:
        db.cleanup()
        db._database.erase()

def test_clientdb_length():
    db = setup_clientdb()
    with open('testdata_clientdb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[s] = td[s]
        # Length
        assert len(td) == len(db)
    finally:
        db.cleanup()
        db._database.erase()

def test_clientdb_delete():
    db = setup_clientdb()
    with open('testdata_clientdb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[s] = td[s]
        # Delete
        key = list(td.keys())[0]
        del db[key]
        assert len(td) - 1 == len(db)
        assert key not in db
    finally:
        db.cleanup()
        db._database.erase()