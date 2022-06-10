from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.template import Loader
from functools import partial
from tornado_swagger.setup import setup_swagger

# from base.database.ssixadb import StatisticsLoggerDB
from base.database.ssixadb import StatisticsLoggerDB
from settings import Settings, LogSettings
from urls import url_patterns, nonprod_url_patterns
from base.oidcprovider import SSIXAOIDCProvider
from base.samlprovider import SSIXASAMLProvider
from base.verification.verificationbase import VerificationMethodManager
from trust.trust import SimpleTrustModel, AttributeAggregationTrustModel
from base.database.basedb import SSIXASQLBaseDB
from base.database.ssixadb import SSIXADB
# from . import version as ver

# Verification modules
from base.verification.email import SimpleEmailVerification
from base.verification.ldap import LDAPVerification

# UI Modules
from handlers.modules.header import HeaderModule
from handlers.modules.menu import MenuModule
from handlers.modules.footer import FooterModule

import signal
import atexit
import argparse
import os.path
import yaml
import ssl
import logging
import logging.config

log = logging.getLogger(__name__)

class SSIXA(Application):

    def __init__(self, config, **kwargs):
        settings = self.load_configuration(config)

        if kwargs['port'] != 80:
            settings['url'] = settings['url'] + ":" + str(kwargs['port'])

        urls = url_patterns
        if settings['environment'] != 'prod':
            urls.extend(nonprod_url_patterns)
            setup_swagger(urls)

        Application.__init__(self, urls, **settings)
        self.initialize_baseobjects()

    def load_configuration(self, config):
        if os.path.isfile(config):
            cfg = {}
            with open(config, 'r') as file:
                try:
                    cfg = yaml.load(file)
                except yaml.YAMLError as exc:
                    log.warning("Error during loading of configuration file, proceeding with default values", str(exc))
            log.debug("Config file loaded successfully")
            return Settings(cfg).settings
        else:
            log.warning("Configuration file not found, using default values")
            return Settings().settings

    def initialize_baseobjects(self):
        # Standard initialization
        self.settings['template_loader'] = Loader(self.settings['template_path'])
        self.ui_modules.update({'Header': HeaderModule, 'Menu': MenuModule, 'Footer': FooterModule})

        # Setup all constantly used objects here
        # Setup persistent and temporary database
        self.settings['source_db'] = SSIXASQLBaseDB(self.settings['db']['server'],self.settings['db']['port'],
                                                    self.settings['db']['user'], self.settings['db']['password'],
                                                    self.settings['db']['database'])
        self.settings['source_db'].connect()

        self.settings['db'] = SSIXADB(self.settings['source_db'])

        # Setup verifiers for claims
        self.settings['verificationmanager'] = self.setup_verificationmethods("{0}://{1}".format(self.settings['protocol'],self.settings['url'])
                                                          ,self.settings['verifier_config'])
        # Add statistics logger
        self.settings['statlogger'] = StatisticsLoggerDB(self.settings['db'])
        # Add trust model
        self.settings['trustmodel'] = AttributeAggregationTrustModel(self.settings['source_db'])

        # OIDC Provider
        self.settings['oidc_provider'] = SSIXAOIDCProvider(self.settings)

        # SAML Provider
        self.settings['saml_provider'] = SSIXASAMLProvider(self.settings)

    def setup_tempdb(self):
        return dict(userinfo=dict())

    def setup_verificationmethods(self, baseurl, cfg):
        manager = VerificationMethodManager()

        emailver = SimpleEmailVerification(baseurl, cfg['emailverification'])
        manager.add_verificationmethod(emailver)
        ldapver = LDAPVerification(baseurl, cfg['ldapverification'])
        manager.add_verificationmethod(ldapver)
        manager.start_cleanup()

        return manager

    def stop(self):
        # Stop all services that have scheduled cleanup processes
        self.settings['oidc_provider'].stop()
        self.settings['verificationmanager'].stop()
        self.settings['saml_provider'].stop()

def sigHandler(server, app, sig=None, frame=None):
    io_loop = IOLoop.instance()

    def shutdown():
        server.stop()
        app.stop()
        io_loop.stop()
        log.info("SSIXA stopped")

    io_loop.add_callback_from_signal(shutdown)

def version():
    # Print version
    print(ver)

def printcfg(args):
    # Print effective configuration
    app = SSIXA(args.config, port=args.port)
    print(yaml.dump(app.load_configuration(args.config)))

def main():
    parser = argparse.ArgumentParser(description='SSIXA')
    parser.add_argument('--port', type=int, default='80', help='Listening port of the web server')
    parser.add_argument('--config', type=str, default='dev.config.yaml', help='location of the configuration file')
    parser.add_argument('--logconfig', type=str, default='log-dev.config.yaml', help='location of the logging configuration file')
    parser.add_argument('--version', action='store_true', help='prints the version of ssixa')
    parser.add_argument('--printcfg', action='store_true', help='prints effective configuration of ssixa')
    args = parser.parse_args()

    # Setup logging
    with open(args.logconfig, 'r') as f:
        config = LogSettings(yaml.load(f.read()))
        logging.config.dictConfig(config.logsettings)

    if args.version:
        version()
    elif args.printcfg:
        printcfg(args)
    else:
        # Start application
        app = SSIXA(args.config, port=args.port)

        ssl_ctx = None
        if app.settings['protocol'] == 'https':
            log.debug("Using HTTPS")
            ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(
                certfile=app.settings['certificate']['certname'],
                keyfile=app.settings['certificate']['keyname'])
            log.debug("Certificate: " + app.settings['certificate']['certname'])
            log.debug("Key name: " + app.settings['certificate']['certname'])

        http_server = HTTPServer(app, ssl_options=ssl_ctx)

        signal.signal(signal.SIGTERM, partial(sigHandler, http_server, app))
        signal.signal(signal.SIGINT, partial(sigHandler, http_server, app))
        atexit.register(sigHandler, http_server, app)

        http_server.listen(args.port)
        log.info("SSIXA is serving on port " + str(args.port))
        IOLoop.instance().start()

if __name__ == '__main__':
    main()