class Settings:
    def __init__(self, config={}):
        self.settings = DEFAULT_CONFIGURATION
        self.apply_configuration(config)

    def apply_configuration(self, config):
        self.settings.update(config)

class LogSettings:
    def __init__(self, config={}):
        self.logsettings = DEFAULT_LOG_CONFIGURATION
        self.apply_configuration(config)

    def apply_configuration(self, config):
        self.logsettings.update(config)

DEFAULT_LOG_CONFIGURATION=dict(
    version=1,
    disable_existing_loggers=False,
    formatters=dict(simple=dict(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')),
    handlers=dict(
        console=
        {"class": "logging.StreamHandler",
         "level": "DEBUG",
         "formatter": "simple",
         "stream": "ext://sys.stdout"}),
    loggers=dict(
        simpleLogger=dict(
            level="DEBUG",
            handlers=["console"],
            propagate="no")),
    root=dict(
        level="DEBUG",
        handlers=["console"])
)

DEFAULT_CONFIGURATION=dict(
    proxymode=False,
    environment="dev",
    debug=True,
    protocol="http",
    static_path="static",
    template_path="templates",
    url="",
    loglevel="debug",
    cookie_secret="",
    xsrf_cookies=False,
    verify_ssl=False,
    db=dict(
        server="",
        port="",
        user="",
        password="",
        database=""),
    certificate=dict(
        certname="",
        keyname="",
        password=""),
    oidc_config=dict(
        code_ttl=2,
        jwks=dict(
            keys=[dict(
                name="",
                password="",
                type="",
                use=["enc", "sig"])],
            name=""),
        verify_client=False,
        verify_ssl=False,
        token_lifetime=3600,
        token_refresh_time=21600,
        token_secret="",
        token_password=""),
    saml_config=dict(
        entityid="",
        description="",
        valid_for=2000,
        debug=1,
        key_file="",
        cert_file="",
        verify_ssl_cert=False,
        sign_response=False,
        metadata=dict(local=[]),
        default_claims=['email','name'],
        service=dict(
            idp=dict(
                name="",
                policy=dict(
                    default=dict(
                        lifetime=dict(
                            minutes=15),
                        attribute_restrictions=None))))),
    authmethodcfg=dict(
        default="uport",
        uport=dict(
            appname="",
            appid="",
            key="",
            proxy_url=""),
        jolocom=dict(
            appid="",
            seed="",
            passphrase="",
            proxy_url=""),
        lissi=dict(
            acapy_admin_url="",
            acapy_inbound_url="",
            did="",
            schema_id="",
            schema_version="",
            cred_def_id="",
            did_autocreate=True)),
    verifier_config=dict(
        emailverification=dict(
            server="",
            port="",
            fromAddress="",
            username="",
            password="",
            debug=True),
        ldapverification=dict(
            server="",
            port="",
            protocol="",
            basedn=""))
    )



