from ssixa.base.verification.ldap import LDAPVerification

import yaml

def setup_config():
    with open('../../../configs/dev.config.yaml', 'r') as f:
        cfg = yaml.load(f.read())
    config = cfg['verifier_config']['ldapverification']

    assert config is not None
    return config

def test_email():
    baseurl = "https://localhost"
    ldapVerifier= LDAPVerification(baseurl, setup_config())

    ldapVerifier('Andreas.Gruener','')
    assert 'Andreas.Gruener' in ldapVerifier.db
    assert not ldapVerifier.db['Andreas.Gruener']['name'] == ''
    assert ldapVerifier.db['Andreas.Gruener']['verified']