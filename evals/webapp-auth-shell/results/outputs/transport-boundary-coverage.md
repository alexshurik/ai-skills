# Recorded transport-boundary response

Finding (`MAJOR`):

`POST /login/start` constructs a limiter key, chooses limit/window settings,
calls the limiter, branches on its result, and only then invokes the login
capability. Hiding the mechanism behind `IpRateLimitService` does not make this
transport-only logic. The response required one application capability or an
approved framework hook.

The same inventory reported `POST /login/claim` for orchestrating nonce
consumption, raw dictionary construction, user persistence lookup, session
issuance, and response projection instead of one claim-login capability.
