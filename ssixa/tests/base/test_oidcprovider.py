from ssixa.base.oidcprovider import SSIXAOIDCProvider

import yaml

def setup_db():
    pass

def setup_config():
    with open('../../../configs/dev.config.yaml', 'r') as f:
        cfg = yaml.load(f.read())
    assert cfg is not None
    return cfg

def test_oidcprovider():
    cfg = setup_config()
    cfg['source_db'] = setup_db()
    cfg['stat_logger'] = ''

    prov = SSIXAOIDCProvider(cfg)


