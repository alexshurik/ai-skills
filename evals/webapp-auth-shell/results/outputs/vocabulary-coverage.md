# Recorded application-vocabulary response

Finding (`MAJOR`):

`LoginNonceService` names an application use case after an intermediate technical
state carrier. Its stakeholder-visible capability is starting, tracking,
confirming, and completing assisted sign-in. The response required a
capability-oriented application-service name and kept nonce terminology behind
the persistence adapter.

`SessionService` retained a capability-oriented class name, but its public
mechanism methods (`generate_jwt`, `decode`, cookie mutation, raw payload lookup)
were separately reported for leaking infrastructure vocabulary through the
application surface.
