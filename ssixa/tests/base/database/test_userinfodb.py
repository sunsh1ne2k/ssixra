from ssixa.base.database.userinfodb import UserInfoDB
from ssixa.base.database.basedb import SSIXASQLBaseDB
from ssixa.base.database.oidcdbobject import OIDCUser, OIDCAttribute

import json
import random
import string

def setup_userinfodb():
    database_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    with open('db_connection.json', 'r') as f:
        conn = json.loads(f.read())

    source_db = SSIXASQLBaseDB(conn['server'],conn['port'],conn['user'],conn['password'],database_name)
    source_db.connect()
    source_db.initialize()

    db = UserInfoDB(source_db)

    assert db is not None
    return db

def test_userinfodb_setget():
    db = setup_userinfodb()
    with open('testdata_userinfodb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        for s in td:
            db[s] = td[s]
        for s in td:
            assert td[s] == db[s]
    finally:
        db.cleanup()
        db._database.erase()

def test_userinfodb_call():
    db = setup_userinfodb()
    with open('testdata_userinfodb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        for s in td:
            db[s] = td[s]
        for s in td:
            cmp_dic = {"age":td[s]["age"],"address":td[s]["address"]}
            assert cmp_dic == db(s,client_id = None, user_info_claims = {"age":"","address":""})
    finally:
        db.cleanup()
        db._database.erase()

def test_userinfodb_addclaims():
    db = setup_userinfodb()
    with open('testdata_userinfodb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        for s in td:
            db[s] = td[s]
            db.add_claims(s,{"number":"50"},client="test_client")
        for s in td:
            n_in_at = False
            d = db[s]
            for att in d:
                if att == "number":
                    n_in_at = True
                else:
                    assert att in td[s].keys()
            assert n_in_at == True
    finally:
        db.cleanup()
        db._database.erase()

def test_userinfodb_removeclaims():
    db = setup_userinfodb()
    with open('testdata_userinfodb.json', 'r') as f:
        td = json.loads(f.read())

    assert isinstance(td, dict)

    try:
        for s in td:
            db[s] = td[s]
            db.remove_claims(s,{"age":"50"})
        for s in td:
            d = db[s]
            assert "age" not in d
    finally:
        db.cleanup()
        db._database.erase()

def test_userinfodb_client_id_to_uid():
    db = setup_userinfodb()

    try:
        db["123456"] = {"name":"test","age":"20"}
        db.add_client_id_to_uid("123456","c1")
        db.add_client_id_to_uid("123456", "c2")
        db.add_client_id_to_uid("123456", "c3")

        assert db.uid_for_client_id_exist("123456","c1")
        assert db.uid_for_client_id_exist("123456","c2")
        assert db.uid_for_client_id_exist("123456","c3")

        db.remove_client_id_from_uid("123456", "c3")
        assert db.uid_for_client_id_exist("123456","c1")
        assert db.uid_for_client_id_exist("123456","c2")
        assert not db.uid_for_client_id_exist("123456","c3")
    finally:
        db.cleanup()
        db._database.erase()

def test_userinfodb_delete():
    db = setup_userinfodb()

    try:
        db["123456"] = {"name":"test","age":"20"}
        del db["123456"]
        assert db["123456"] == None
    finally:
        db.cleanup()
        db._database.erase()

def test_userinfodb_cleanup():
    db = setup_userinfodb()

    try:
        db["123456"] = {"name":"test","age":"20"}
        db.cleanup()
        assert db["123456"] == None
    finally:
        db.cleanup()
        db._database.erase()

def test_userinfodb_contain():
    db = setup_userinfodb()

    try:
        db["123456"] = {"name": "test", "age": "20"}
        assert "123456" in db
    finally:
        db.cleanup()
        db._database.erase()