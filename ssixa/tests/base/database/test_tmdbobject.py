from ssixa.base.database.tmdbobject import TMAttribute, TMProvider, TMDID

import json


def test_tmdbobject_tmattribute():
    with open('testdata_tmdbobject.json', 'r') as f:
        td = json.loads(f.read())
    assert isinstance(td, dict)

    attributes = td['tmattribute']
    for s in attributes:
        c = TMAttribute.fromDict(attributes[s])
        assert attributes[s] == c.toDict()

def test_tmdbobject_tmprovider():
    with open('testdata_tmdbobject.json', 'r') as f:
        td = json.loads(f.read())
    assert isinstance(td, dict)

    providers = td['tmprovider']
    for p in providers:
        c = TMProvider.fromDict(providers[p])
        assert providers[p] == c.toDict()

