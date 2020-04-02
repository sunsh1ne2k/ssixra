from ssixa.base.samlprovider import SSIXASAMLProvider
from http.cookies import SimpleCookie
from saml2 import time_util
from saml2.s_utils import rndstr

import re
import yaml
import base64

def setup_db():
    pass

def setup_config():
    with open('../../../configs/dev.config.yaml', 'r') as f:
        cfg = yaml.load(f.read())
    assert cfg is not None
    return cfg

def test_samlprovider():
    cfg = setup_config()
    cfg['source_db'] = setup_db()
    cfg['stat_logger'] = ''

    prov = SSIXASAMLProvider(cfg)

def test_samplprovider_():
    pass