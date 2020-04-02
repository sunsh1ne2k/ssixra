from oic.utils.client_management import CDB
from oic.utils.userinfo import UserInfo
from ssixa.base.database.ssixadb import SSIXADB

import logging
log = logging.getLogger(__name__)

class ClientDictDB(CDB):

    def __init__(self, filename):
        super(ClientDictDB, self).__init__(filename)

    def __delitem__(self, key):
        log.debug("Delete key: " + str(key))
        del self.cdb[key]

    def __setitem__(self, key, value):
        log.debug("Set key: " + str(key))
        log.debug("Set value: " + str(value))
        self.cdb[key] = value


class UserInfoDictDB(UserInfo):

    def __init__(self):
        super(UserInfoDictDB, self).__init__({})

    def add_claims(self, userid, claims):
        log.debug("User Id: " + str(userid))
        log.debug("Claims: " + str(claims))
        assert type(claims) == dict

        if not userid in self.db:
            self.db[userid] = dict()

        self.db[userid].update(claims)
        log.debug("Update successful")

class SSIXADictDB(SSIXADB):

    def __init__(self):
        super(SSIXADictDB, self).__init__({})

        self.db = {}

    def __delitem__(self, key):
        log.debug("Delete key: " + str(key))
        del self.db[key]

    def __getitem__(self, key):
        log.debug("Get key: " + str(key))

        if key in self.db:
            return self.db[key]
        else:
            return None

    def __setitem__(self, key, value):
        log.debug("Key: " + str(key))
        log.debug("Value: " + str(value))
        self.db[key] = value

    def add_entry(self, table, object, attribute, value):
        log.debug("Table: " + str(table))
        log.debug("Object: " + str(object))
        log.debug("Attribute: " + str(attribute))
        log.debug("Value: " + str(value))
        if self.db is None:
            self.db = dict()
        if table not in self.db:
            self.db[table] = dict()
        if object not in self.db[table]:
            self.db[table][object] = dict()
        self.db[table][object][attribute] = value

    def get_entry(self, table, object, attribute):
        log.debug("Table: " + str(table))
        log.debug("Object: " + str(object))
        log.debug("Attribute: " + str(attribute))
        log.debug(table, object, attribute)
        try:
            return self.db[table][object][attribute]
        except:
            return None

    def get_object(self, table, object):
        log.debug("Table: " + str(table))
        log.debug("Object: " + str(object))

        try:
            return self.db[table][object]
        except:
            return None

    def get_filtered_entry(self, type, object, **filter):
        pass

    def delete_entry(self, type, object, attribute):
        log.debug("Type: " + str(type))
        log.debug("Object: " + str(object))
        log.debug("Attribute: " + str(attribute))

        try:
            del self.db[type][object][attribute]
        except:
            pass





