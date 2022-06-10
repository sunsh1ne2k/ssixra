from oic.utils.clientdb import BaseClientDatabase
from base.database.basedb import SSIXADBBase
from base.database.oidcdbobject import OIDCClient

import logging

log = logging.getLogger(__name__)

class ClientDB(BaseClientDatabase, SSIXADBBase):

    def __init__(self, db):
        BaseClientDatabase.__init__(self)
        SSIXADBBase.__init__(self, db)

    def __getitem__(self, key):
        log.debug("Key: " + str(key))
        # Retrieve an item by a key. Raises KeyError if item not found.
        s = None
        clients = None
        item = None
        try:
            s = self.get_session()
            clients = s.query(OIDCClient).filter(OIDCClient.client_id == key).all()
            log.debug("Retrieved clients: "+ str(len(clients)))
        except Exception as e:
            log.exception("Could not retrieve clients")
        finally:
            s.close()

        if clients is not None and len(clients) == 1:
            item = clients[0].toDict()
        else:
            log.error("Client not found")
        log.debug("Client: " + str(item))
        return item

    def get(self, key, default=None):
        log.debug("Key: " + str(key))
        # Retrieve an item by a key. Return default if not found.
        s = None
        clients = None
        try:
            s = self.get_session()
            clients = s.query(OIDCClient).filter(OIDCClient.client_id == key).all()
            log.debug("Retrieved clients: " + str(len(clients)))
        except Exception as e:
            log.debug(str(e))
        finally:
            if s is not None:
                s.close()

        if clients is not None and len(clients) == 1:
            item = clients[0].toDict()
        else:
            item = default
            log.error("Client not found.")

        log.debug("Client: " + str(item))
        return item

    def __setitem__(self, key, value):
        log.debug("Key: " + str(key))
        log.debug("Value: " + str(value))
        # Set key with value.
        s = None
        try:
            s = self.get_session()
            client = OIDCClient.fromDict(value)
            s.add(client)
            s.commit()
        except Exception as e:
            log.exception("Commit failed")
        finally:
            if s is not None:
                s.close()

    def __delitem__(self, key):
        log.debug("Key: " + str(key))
        # Remove key from database.
        s = None
        try:
            s = self.get_session()
            clients = s.query(OIDCClient).filter(OIDCClient.client_id == key).all()
            if len(clients) == 1:
                s.delete(clients[0])
            s.commit()
        except Exception as e:
            log.exception("Commit failed")
        finally:
            if s is not None:
                s.close()

    def __contains__(self, key):
        log.debug("Key: " + str(key))
        # Return True if key is contained in the database.
        s = None
        count=0
        try:
            s = self.get_session()
            clients = s.query(OIDCClient).filter(OIDCClient.client_id == key).all()
            count = len(clients)
            log.debug("Count: " + str(count))
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()

        if count > 0:
            log.debug("Result: True")
            return True
        else:
            log.debug("Result: False")
            return False

    def keys(self):
        # Return all contained keys.
        keys = []
        s = None
        try:
            s = self.get_session()
            clients = s.query(OIDCClient).all()
            for c in clients:
                keys.append(c.client_id)
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()
        log.debug("Keys" + str(keys))
        return keys

    def items(self):
        # Return list of all contained items.
        pass  # pragma: no cover

    def __len__(self):
        # Return number of contained keys.
        s = None
        count = 0
        try:
            s = self.get_session()
            clients = s.query(OIDCClient).all()
            count = len(clients)
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()

        log.debug("Count: " + str(count))
        return count

    def cleanup(self):
        log.debug("Database cleanup")
        s = None
        try:
            s = self.get_session()
            clients = s.query(OIDCClient).filter(OIDCClient.instance == self.instance).all()
            for c in clients:
                s.delete(c)
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()