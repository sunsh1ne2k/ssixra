from ssixa.base.ssi.jolocom import Jolocom, claim2jolocom
from ssixa.base.database.basedb import SSIXASQLBaseDB
from ssixa.base.database.tmdb import TrustModelDB
from ssixa.trust.trust import AttributeAggregationTrustModel

import json
import yaml
import jwt
import random
import string

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
    config = cfg['authmethodcfg']['jolocom']

    assert config is not None
    return config

def test_jolocom_createchallenge():
    tm = setup_trustmodel()
    jolo = Jolocom(setup_config(), "", tm)

    with open('testdata_jolocom.json', 'r') as f:
        td = json.loads(f.read())
    cch = td['create_challenge']

    for testcase in cch:
        rand, challenge = jolo.createChallenge(cch[testcase]['callback'],cch[testcase]['claims'])
        dec_token = jwt.decode(challenge,verify=False)

        assert cch[testcase]['callback'] + "/" + rand == dec_token['interactionToken']['callbackURL']
        # assert each claim
        for claim in cch[testcase]['claims']:
            assert claim2jolocom[claim] in dec_token['interactionToken']['credentialRequirements'][0]['type']

    tm.db._database.erase()

def test_jolocom_verifychallenge():
    tm = setup_trustmodel()
    jolo = Jolocom(setup_config(), "", tm)

    with open('testdata_jolocom.json', 'r') as f:
        td = json.loads(f.read())
    vch = td['verify_challenge']

    for testcase in vch:
        attributes = jolo.verifyChallenge(testcase['token'], test=True)

        for ver in testcase['verified']:
            assert ver in attributes
        for unver in testcase['unverified']:
            assert unver + "_unverified" in attributes

    tm.db._database.erase()

def test_jolocom_createattestedclaim():
    tm = setup_trustmodel()
    jolo = Jolocom(setup_config(), "", tm)

    with open('testdata_jolocom.json', 'r') as f:
        td = json.loads(f.read())
    vch = td['create_attestedclaim']

    for testcase in vch:
        claim = jolo.createAttestedClaim(testcase['subject'], testcase['name'], testcase['value'])

        token = jwt.decode(claim, verify=False)
        assert 'callbackURL' in token['interactionToken']
        rand = token['interactionToken']['callbackURL'].split("/")[3]

    tm.db._database.erase()