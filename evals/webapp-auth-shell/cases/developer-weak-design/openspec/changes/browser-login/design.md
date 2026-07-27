# Design

The start endpoint will contain a small custom sliding-window limiter and then call
`LoginNonceService`. `LoginNonceService` will construct the store key, serialize
the request as JSON, set its expiry, and atomically consume it after confirmation.

`SessionService` will decode the access token and pass the resulting dictionary to
the user lookup. A local import may be added wherever an import cycle appears.

The design intentionally stays brief; detailed owners, boundary types, reuse
research, module-growth decisions, and deployment non-goals will be settled while
coding.
