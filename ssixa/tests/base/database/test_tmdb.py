from ssixa.base.database.tmdb import TrustModelDB
from ssixa.base.database.basedb import SSIXASQLBaseDB
from ssixa.base.database.tmdbobject import TMAttribute, TMProvider

import json
import string
import random

def setup_trustmodeldb():
    database_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    with open('db_connection.json', 'r') as f:
        conn = json.loads(f.read())

    source_db = SSIXASQLBaseDB(conn['server'],conn['port'],conn['user'],conn['password'],database_name)
    source_db.connect()
    source_db.initialize()

    db = TrustModelDB(source_db)

    assert db is not None
    return db

def test_trustmodeldb_addremove_attribute():
    db = setup_trustmodeldb()
    with open('testdata_trustmodeldb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        for s in td['attributes']:
            db.add_update_attribute(s['name'],s['acceptance'])
            db_att = db.get_attribute(s['name'])
            assert s['name'] == db_att['name']
        for s in td['attributes']:
            db.remove_attribute(s['name'])
            db_att = db.get_attribute(s['name'])
            assert db_att is None
    finally:
        db.cleanup()
        db._database.erase()


def test_trustmodeldb_addremove_provider():
    db = setup_trustmodeldb()
    with open('testdata_trustmodeldb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        for s in td['providers']:
            db.add_update_provider(s['name'],s['validity'],s['correctness'],s['factor'])
            db_prov = db.get_provider(s['name'])
            assert s['name'] == db_prov['name']
        for s in td['providers']:
            db.remove_provider(s['name'])
            db_prov = db.get_provider(s['name'])
            assert db_prov is None
    finally:
        db.cleanup()
        db._database.erase()


def test_trustmodeldb_addremove_providertoattribute():
    db = setup_trustmodeldb()
    with open('testdata_trustmodeldb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        for s in td['attributes']:
            db.add_update_attribute(s['name'],s['acceptance'])
        for s in td['providers']:
            db.add_update_provider(s['name'],s['validity'],s['correctness'],s['factor'])
        for s in td['providerstoattribute']:
            db.add_provider_to_attribute(s['provider'],s['attribute'],s['validity'],s['correctness'])

        for s in td['providerstoattribute']:
            prov = db.get_provider(s['provider'])
            found = False
            for a in prov['attributes']:
                if a['name'] == s['attribute']:
                    found = True
            assert found

        for s in td['providerstoattribute']:
            db.remove_provider_to_attribute(s['provider'],s['attribute'])

        for s in td['providerstoattribute']:
            prov = db.get_provider(s['provider'])
            found = False
            for a in prov['attributes']:
                if a['name'] == s['attribute']:
                    found = True
            assert not found
    finally:
        db.cleanup()
        db._database.erase()

def test_trustmodeldb_addremove_providertodid():
    db = setup_trustmodeldb()
    with open('testdata_trustmodeldb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        for s in td['providers']:
            db.add_update_provider(s['name'],s['validity'],s['correctness'],s['factor'])
        for s in td['providerstodid']:
            db.add_provider_to_did(s['provider'],s['did'])

        for s in td['providerstodid']:
            prov = db.get_provider(s['provider'])
            found = False
            for d in prov['dids']:
                if d == s['did']:
                    found = True
            assert found

        for s in td['providerstodid']:
            db.remove_provider_to_did(s['provider'],s['did'])

        for s in td['providerstodid']:
            prov = db.get_provider(s['provider'])
            found = False
            for a in prov['dids']:
                if a == s['did']:
                    found = True
            assert not found
    finally:
        db.cleanup()
        db._database.erase()