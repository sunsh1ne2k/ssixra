from saml2.mdstore import MetadataStore


import logging
log = logging.getLogger(__name__)


class MetaDataStoreDB(MetadataStore):

    def __init__(self, db, attrc, config):
        super(MetaDataStoreDB, self).__init__(attrc, config)

        self.db = db


    def load_from_database(self):
        pass