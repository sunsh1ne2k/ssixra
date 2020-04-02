from ssixa.base.database.oidcdbobject import OIDCClient, OIDCAttribute, OIDCSession, OIDCUidToSid, OIDCUser

import json


def test_oidcdbobject_oidcclient():
    with open('testdata_oidcdbobject.json', 'r') as f:
        td = json.loads(f.read())
    assert isinstance(td, dict)

    clients = td['oidcclient']
    for s in clients:
        # Generate client from Dict
        c = OIDCClient.fromDict(clients[s])
        assert clients[s] == c.toDict()

def test_oidcdbobject_oidcuser_fromtodict():
    with open('testdata_oidcdbobject.json', 'r') as f:
        td = json.loads(f.read())
    assert isinstance(td, dict)

    users = td['oidcuser']
    for s in users:
        # Generate user from Dict
        u = OIDCUser.fromDict(s,users[s]['attributes'])
        # Generate Dict from user
        assert users[s]['attributes'] == u.toDict()
        u = OIDCUser.fromDict(s,users[s]['attributes'],users[s]['client_id'])
        assert users[s]['attributes'] == u.toDict()
        u = OIDCUser.fromDict(s,users[s]['attributes'],users[s]['client_id'],users[s]['instance'])
        assert users[s]['attributes'] == u.toDict()

def test_oidcdbobject_oidcuser_hash():
    u1 = OIDCUser.fromDict("user1", {})
    u2 = OIDCUser.fromDict("user1", {})
    assert u1.__hash__() == u2.__hash__()
    u1 = OIDCUser.fromDict("user1", {})
    u2 = OIDCUser.fromDict("user2", {})
    assert u1.__hash__() != u2.__hash__()
    u1 = OIDCUser.fromDict("user1", {}, client_id="client1")
    u2 = OIDCUser.fromDict("user1", {}, client_id="client2")
    assert u1.__hash__() != u2.__hash__()
    u1 = OIDCUser.fromDict("user1", {}, client_id="client1")
    u2 = OIDCUser.fromDict("user1", {}, client_id="client1")
    assert u1.__hash__() == u2.__hash__()

def test_oidcdbobject_oidcuser_string():
    u1 = OIDCUser.fromDict("user1", {})
    assert "user1" == str(u1)
    assert "user2" != str(u1)

def test_oidcdbobject_oidcuser_equal():
    u1 = OIDCUser.fromDict("user1", {})
    u2 = OIDCUser.fromDict("user1", {})
    assert u1 == u2
    u1 = OIDCUser.fromDict("user1", {})
    u2 = OIDCUser.fromDict("user2", {})
    assert u1 != u2
    u1 = OIDCUser.fromDict("user1", {}, client_id="client1")
    u2 = OIDCUser.fromDict("user1", {}, client_id="client2")
    assert u1 != u2
    u1 = OIDCUser.fromDict("user1", {}, client_id="client1")
    u2 = OIDCUser.fromDict("user1", {}, client_id="client1")
    assert u1 == u2

def test_oidcdbobject_oidcattribute_fromtodict():
    with open('testdata_oidcdbobject.json', 'r') as f:
        td = json.loads(f.read())
    assert isinstance(td, dict)

    attributes = td['oidcattribute']
    ls = OIDCAttribute.fromDictToListofOIDCAttributes(attributes)
    for att in ls:
        assert attributes[att.attribute] == att.value

def test_oidcdbobject_oidcattribute_hash():
    a1 = OIDCAttribute("name","tom")
    a2 = OIDCAttribute("name","tom")
    assert a1.__hash__() == a2.__hash__()
    a1 = OIDCAttribute("lastname", "tom")
    a2 = OIDCAttribute("firstname", "tom")
    assert a1.__hash__() != a2.__hash__()

def test_oidcdbobject_oidcattribute_equal():
    a1 = OIDCAttribute("name", "tom")
    a2 = OIDCAttribute("name", "tom")
    assert a1 == a2
    a1 = OIDCAttribute("lastname", "tom")
    a2 = OIDCAttribute("firstname", "tom")
    assert a1 != a2

def test_oidcdbobject_oidcattribute_string():
    a1 = OIDCAttribute("name", "tom")
    assert str(a1) == "name"
    assert str(a1) != "name1"

def test_oidcdbobject_oidcsession_fromtodict():
    with open('testdata_oidcdbobject.json', 'r') as f:
        td = json.loads(f.read())
    assert isinstance(td, dict)

    sessions = td['oidcsession']
    for sess in sessions:
        s = OIDCSession.fromDict(sess,sessions[sess])
        assert sessions[sess] == s.toDict()

def test_oidcdbobject_oidcsession_equal():
    s1 = OIDCSession("11")
    s2 = OIDCSession("11")
    assert s1 == s2
    s1 = OIDCSession("11")
    s2 = OIDCSession("22")
    assert s1 != s2

def test_oidcdbobject_oidcsession_string():
    s1 = OIDCSession("11")
    s2 = OIDCSession("11")
    assert str(s1) == str(s2)
    s1 = OIDCSession("11")
    s2 = OIDCSession("22")
    assert str(s1) != str(s2)

def test_oidcdbobject_oidcsession_hash():
    s1 = OIDCSession("11")
    s2 = OIDCSession("11")
    assert s1.__hash__() == s2.__hash__()
    s1 = OIDCSession("11")
    s2 = OIDCSession("22")
    assert s1.__hash__() != s2.__hash__()

