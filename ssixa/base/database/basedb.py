from ssixa.base.database.basedbobject import BaseStatistic
from ssixa.base.database import SSIXASQLBaseDBBase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import logging
log = logging.getLogger(__name__)


class SSIXADBBase(object):

    def __init__(self, db):
        self._database = db

    def get_session(self):
        return self._database.get_session()

class SSIXASQLBaseDB(object):

    def __init__(self, server, port, user, password, database):
        self.server = server
        log.debug("Server: " + str(server))
        self.port = port
        log.debug("Port: " + str(port))
        self.user = user
        log.debug("User: " + str(user))
        self.password = password
        log.debug("Password: *****")
        self.database = database
        log.debug("Database: " + str(database))

    def connect(self):
        self.engine = create_engine('postgresql://{0}:{1}@{2}:{3}/{4}'.format(
            self.user,
            self.password,
            self.server,
            self.port,
            self.database
        ))
        self.Session = sessionmaker(bind=self.engine)
        log.debug("Database session established")

    def disconnect(self):
        log.debug("Database sessions closed")
        self.Session.close_all()

    def initialize(self):
        # Create database
        engine = create_engine('postgresql://{0}:{1}@{2}:{3}/postgres'.format(
            self.user,
            self.password,
            self.server,
            self.port,
        ))
        conn = engine.connect()
        conn.execute("commit")

        try:
            conn.execute("create database {0}".format(self.database))
            log.debug("Database created")
        except Exception as ex:
            log.exception("Could not create database ")
        else:
            conn.close()

        # Create database schema
        self.connect()
        SSIXASQLBaseDBBase.metadata.create_all(self.engine)
        self.Session.close_all()
        log.debug("Database schema created")

    def erase(self):
        # delete database
        engine = create_engine('postgresql://{0}:{1}@{2}:{3}/postgres'.format(
            self.user,
            self.password,
            self.server,
            self.port,
        ))
        conn = engine.connect()
        conn.execute("commit")

        try:
            conn.execute("drop database {0}".format(self.database))
        except:
            log.exception("Could not drop database")
        else:
            conn.close()

    def get_session(self):
        # Test query to activate connection if passive
        s = None
        try:
            s = self.Session()
            s.query(BaseStatistic).limit(1).all()
        except Exception as e:
            log.warning("Reactivate DB session",exc_info=True)
        finally:
            if s is not None:
                s.close()
        return self.Session()