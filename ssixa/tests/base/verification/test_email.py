from ssixa.base.verification.verificationbase import VerificationMethodManager
from ssixa.base.verification.email import SimpleEmailVerification

import yaml
import json
import re
import base64

def setup_config():
    with open('../../../configs/dev.config.yaml', 'r') as f:
        cfg = yaml.load(f.read())
    config = cfg['verifier_config']['emailverification']

    assert config is not None
    return config

def test_email():
    baseurl = "https://localhost"
    simpleEmail = SimpleEmailVerification(baseurl, setup_config(), testmode=True)

    td = None
    with open('testdata_email.json', 'r') as f:
        td = json.loads(f.read())

    for testcase in td:
        simpleEmail(testcase['name'],testcase['email'])

        out = simpleEmail.testoutput
        assert out['recipient'] == testcase['email']
        enc_text = re.search('(?<=base64\s\s)[0-9a-zA-Z\s]*',out['text']).group()
        dec_text = base64.b64decode(enc_text).decode()
        random = re.search('(?<=/)[0-9a-zA-Z]*$',dec_text).group()

        assert not simpleEmail.verification_completed(testcase['name'])
        simpleEmail.process_verification(random)
        assert simpleEmail.verification_completed(testcase['name'])
        assert testcase['email'] == simpleEmail.get_claim_value(testcase['name'])