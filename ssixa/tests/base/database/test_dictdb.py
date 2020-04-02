from ssixa.base.database.dictdb import ClientDictDB, UserInfoDictDB, SSIXADictDB

import json


def test_dictdb_clientdictdb_setget():
    #db = ClientDictDB("../../dev-ressource/cdb")
    #db['client1'] = dict(name='testname',client_salt='asdasdas')
    #assert db['client1'] == dict(name='testname',client_salt='asdasdas')
    pass

def test_dictdb_clientdictdb_delete():
    #db = ClientDictDB("../../dev-ressource/cdb")
    #db['client1'] = dict(name='testname',client_salt='asdasdas')
    #del db['client1']
    #assert 'client1' not in db
    pass

def test_userinfodictdb_addclaims():
    db = UserInfoDictDB()

    # Case 1 - user has no claims
    db.add_claims("user0",dict(firstname='tom',lastname='mayer'))
    assert db('user0',None) == dict(firstname='tom',lastname='mayer')
    # Case 2 - user has already claims
    db.add_claims("user0",dict(age='34',city='berlin'))
    assert db('user0', None) == dict(firstname='tom',lastname='mayer',age='34',city='berlin')

def test_ssixadictdb_setget():
    db = SSIXADictDB()

    db['user'] = dict(name='tom',lastname='meyer')
    assert db['user'] == dict(name='tom',lastname='meyer')

def test_ssixadictdb_addgetdeleteentry():
    db = SSIXADictDB()

    db.add_entry("user","user1","firstname","tom")
    db.add_entry("user","user1","lastname","meyer")
    assert db.get_entry("user","user1","firstname") == "tom"

    db.delete_entry("user","user1","firstname")
    assert db.get_entry("user", "user1", "lastname") == "meyer"
    assert db.get_entry("user", "user1", "firstname") == None

def test_ssixadictdb_getobject():
    db = SSIXADictDB()

    db.add_entry("user","user1","firstname","tom")
    db.add_entry("user","user1","lastname","meyer")
    assert db.get_object("user","user1") == dict(firstname="tom", lastname="meyer")
