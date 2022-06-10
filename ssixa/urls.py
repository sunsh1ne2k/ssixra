from tornado.web import url

from handlers.oidc import (
    OIDCAuthorizationHandler,
    OIDCTokenHandler,
    OIDCUserInfoHandler,
    OIDCRegistrationHandler,
    OIDCEndSessionHandler,
    OIDCConfigurationHandler,
    OIDCWebfingerHandler)
from handlers.saml import (
    SAMLSSOPostHandler,
    SAMLSSORedirectHandler,
    SAMLSLOPostHandler,
    SAMLSLORedirectHandler)
from handlers.oidc_blockchain import (
    OIDCBlockchainAuthCreateChallengeHandler,
    OIDCBlockchainAuthVerificationHandler,
    OIDCBlockchainAuthSideChannelVerificationHandler,
    OIDCBlockchainAuthStatusVerificationHandler,
    BlockchainAuthLissiRoutingHandler,
    BlockchainAuthLissiWebhookConnectionTopicHandler,
    BlockchainAuthLissiWebhookPresentationProofTopicHandler,
    BlockchainAuthLissiWebhookOtherTopicHandler)
from handlers.saml_blockchain import (
    SAMLBlockchainAuthCreateChallengeHandler,
    SAMLBlockchainAuthVerificationHandler,
    SAMLBlockchainAuthSideChannelVerificationHandler,
    SAMLBlockchainAuthStatusVerificationHandler)
from handlers.claims import (
    ClaimsHandler,
    VerifyClaimsHandler,
    GetAttestationClaimsHandler,
    ReceiveJolocomCredentialOfferResponseHandler)
from handlers.verification import SimpleEmailVerificationProcessVerificationHandler

url_patterns = [
    # OIDC provider handlers
    # -> Dispatcher to different authentication methods
    url(r"/oidc/authorization", OIDCAuthorizationHandler),
    url(r"/oidc/token", OIDCTokenHandler),
    url(r"/oidc/userinfo", OIDCUserInfoHandler),
    url(r"/oidc/registration", OIDCRegistrationHandler),
    url(r"/oidc/end_session", OIDCEndSessionHandler),
    url(r"/oidc/.well-known/openid-configuration", OIDCConfigurationHandler),
    url(r"/oidc/.well-known/webfinger", OIDCWebfingerHandler),
    # OIDC blockchain auth handlers
    url(r"/oidc/blockchain/challenge", OIDCBlockchainAuthCreateChallengeHandler),
    url(r"/oidc/blockchain/verification/.*",
        OIDCBlockchainAuthVerificationHandler),
    url(r"/oidc/blockchain/verificationside/.*",
        OIDCBlockchainAuthSideChannelVerificationHandler),
    url(r"/oidc/blockchain/statusverification/.*",
        OIDCBlockchainAuthStatusVerificationHandler),

    # SAML provider handlers
    # SSO
    url(r"/saml/sso/post", SAMLSSOPostHandler),
    url(r"/saml/sso/post/.*", SAMLSSOPostHandler),
    url(r"/saml/sso/redirect", SAMLSSORedirectHandler),
    url(r"/saml/sso/redirect/.*", SAMLSSORedirectHandler),
    # SLO
    url(r"/saml/slo/redirect", SAMLSLORedirectHandler),
    url(r"/saml/slo/redirect/.*", SAMLSLORedirectHandler),
    url(r"/saml/slo/post", SAMLSLOPostHandler),
    url(r"/saml/slo/post/.*", SAMLSLOPostHandler),
    # SAML blockchain auth handlers
    url(r"/saml/blockchain/challenge", SAMLBlockchainAuthCreateChallengeHandler),
    url(r"/saml/blockchain/verification/.*",
        SAMLBlockchainAuthVerificationHandler),
    url(r"/saml/blockchain/verificationside/.*",
        SAMLBlockchainAuthSideChannelVerificationHandler),
    url(r"/saml/blockchain/statusverification/.*",
        SAMLBlockchainAuthStatusVerificationHandler),

    # Specific authorization handlers to reflect more complex flow
    url(r"/blockchain/lissi/routing/.*", BlockchainAuthLissiRoutingHandler),
    url(r"/blockchain/lissi/webhook/topic/connection.*",
        BlockchainAuthLissiWebhookConnectionTopicHandler),
    url(r"/blockchain/lissi/webhook/topic/present_proof",
        BlockchainAuthLissiWebhookPresentationProofTopicHandler),
    url(r"/blockchain/lissi/webhook/.*",
        BlockchainAuthLissiWebhookOtherTopicHandler),

    # Claims management
    # General handlers
    url(r"/claims", ClaimsHandler),
    url(r"/claims/verifyclaim", VerifyClaimsHandler),
    url(r"/claims/getattestation", GetAttestationClaimsHandler),
    # Specific handlers for attestations to reflect more complex flows
    url(r"/claims/jolocom/.*", ReceiveJolocomCredentialOfferResponseHandler),

    # Verification method handlers
    # Email Verification
    url(r"/verification/email/simpleemail/.*",
        SimpleEmailVerificationProcessVerificationHandler),
]

# Extension for non production handlers
nonprod_url_patterns = [
]
