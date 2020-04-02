from ssixa.base.database.sessiondb import SessionDB
from ssixa.base.database.basedb import SSIXASQLBaseDB

import json
import random
import string


def setup_sessiondb():
    database_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    with open('db_connection.json', 'r') as f:
        conn = json.loads(f.read())

    source_db = SSIXASQLBaseDB(conn['server'],conn['port'],conn['user'],conn['password'],database_name)
    source_db.connect()
    source_db.initialize()

    db = SessionDB(source_db,"http://localhost")

    assert db is not None
    return db


def test_sessiondb_setget():
    db = setup_sessiondb()
    with open('testdata_sessiondb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[s] = td[s]
        # Get items and compare
        for s in td:
            assert td[s] == db[s]
        # Update session information
        db['1'] = td['2']
        assert db['1'] == td['2']
    finally:
        db.cleanup()
        db._database.erase()

def test_sessiondb_deletecontains():
    db = setup_sessiondb()
    with open('testdata_sessiondb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        # Set items
        for s in td:
            db[s] = td[s]
        # Check if contains
        for s in td:
            assert s in db
        # Delete item and check if it does not contain anymore
        for s in td:
            del db[s]
            assert s not in db
    finally:
        db.cleanup()
        db._database.erase()

def test_sessiondb_getsidsbysub():
    db = setup_sessiondb()
    with open('testdata_sessiondb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        subs = dict()
        # Set items
        for s in td:
            db[s] = td[s]
            db.uid2sid[''.join(random.choice(string.ascii_lowercase) for i in range(5))] = s
            if td[s]['sub'] not in subs:
                subs[td[s]['sub']] = []
            subs[td[s]['sub']].append(s)
        # Get Sids by sub
        for sub in subs:
            ver_sids = db.get_sids_by_sub(sub)
            for ver_s in ver_sids:
                if ver_s not in subs[sub]:
                    assert False
            for s in subs[sub]:
                if s not in ver_sids:
                    assert False
    finally:
        db.cleanup()
        db._database.erase()

def test_sessiondb_getsidsbysubandclient():
    db = setup_sessiondb()
    with open('testdata_sessiondb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        subs = dict()
        # Set items
        for s in td:
            db[s] = td[s]
            db.uid2sid[''.join(random.choice(string.ascii_lowercase) for i in range(5))] = s
            subandclient = td[s]['sub'] + "," + td[s]['client_id']
            if subandclient not in subs:
                subs[subandclient] = []
            subs[subandclient].append(s)
        # Get Sids by sub and client
        for subandclient in subs:
            ver_sids = db.get_sids_by_sub_and_client(subandclient.split(",")[0],subandclient.split(",")[1])
            for ver_s in ver_sids:
                if ver_s not in subs[subandclient]:
                    assert False
            for s in subs[subandclient]:
                if s not in ver_sids:
                    assert False
    finally:
        db.cleanup()
        db._database.erase()

def test_sessiondb_getsidsbyuidandclient():
    db = setup_sessiondb()
    with open('testdata_sessiondb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        subs = dict()
        uids = []
        # Set items
        for s in td:
            db[s] = td[s]
            uid = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
            db.uid2sid[uid] = s
            uidandclient = uid + "," + td[s]['client_id']
            if uidandclient not in subs:
                subs[uidandclient] = []
            subs[uidandclient].append(s)
        uids =  db.uid2sid.items
        # Get Sids by uid and client
        for uidandclient in subs:
            ver_sids = db.get_sids_by_sub_and_client(uidandclient.split(",")[0],uidandclient.split(",")[1])
            for ver_s in ver_sids:
                if ver_s not in subs[uidandclient]:
                    assert False
            for s in subs[uidandclient]:
                if s not in ver_sids:
                    assert False
    finally:
        db.cleanup()
        db._database.erase()