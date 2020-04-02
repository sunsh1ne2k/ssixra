from ssixa.base.ssi.uport import UPort
from ssixa.base.database.basedb import SSIXASQLBaseDB
from ssixa.base.database.tmdb import TrustModelDB
from ssixa.trust.trust import AttributeAggregationTrustModel

import json
import yaml
import random
import string
import jwt

def setup_trustmodel():
    database_name = ''.join(random.choice(string.ascii_lowercase) for i in range(5))

    with open('db_connection.json', 'r') as f:
        conn = json.loads(f.read())

    source_db = SSIXASQLBaseDB(conn['server'],conn['port'],conn['user'],conn['password'],database_name)
    source_db.connect()
    source_db.initialize()

    db = TrustModelDB(source_db)
    assert db is not None
    tm = AttributeAggregationTrustModel(db)
    assert tm is not None
    return tm

def setup_config():
    with open('../../../configs/dev.config.yaml', 'r') as f:
        cfg = yaml.load(f.read())
    config = cfg['authmethodcfg']['uport']

    assert config is not None
    return config

def test_uport_createchallenge():
    tm = setup_trustmodel()
    uport = UPort(setup_config(), tm)

    with open('testdata_uport.json', 'r') as f:
        td = json.loads(f.read())
    cch = td['create_challenge']

    for testcase in cch:
        rand, challenge = uport.createChallenge(cch[testcase]['callback'],cch[testcase]['claims'])
        token = challenge.split("=")[1]
        dec_token = jwt.decode(token,verify=False)

        assert cch[testcase]['callback'] + "/" + rand == dec_token['callback']
        assert cch[testcase]['claims'] == dec_token['requested']
        assert cch[testcase]['claims'] == dec_token['verified']

    tm.db._database.erase()

def test_uport_verifychallenge():
    tm = setup_trustmodel()
    uport = UPort(setup_config(), tm)

    with open('testdata_uport.json', 'r') as f:
        td = json.loads(f.read())
    vch = td['verify_challenge']

    for testcase in vch:
        attributes = uport.verifyChallenge(testcase['token'], test=True)

        for ver in testcase['verified']:
            assert ver in attributes
        for unver in testcase['unverified']:
            assert unver + "_unverified" in attributes

    tm.db._database.erase()

def test_uport_createattestedclaim():
    tm = setup_trustmodel()
    uport = UPort(setup_config(), tm)

    with open('testdata_uport.json', 'r') as f:
        td = json.loads(f.read())
    vch = td['create_attestedclaim']

    for testcase in vch:
        claim = uport.createAttestedClaim(testcase['subject'],testcase['name'],testcase['value'])
        token = jwt.decode(claim.split("=")[1], verify=False)

        assert token['sub'] == testcase['subject']
        assert testcase['name'] in token['claim']
        assert token['claim'][testcase['name']] == testcase['value']

    tm.db._database.erase()