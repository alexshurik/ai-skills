# Design

The transport adapter maps requests to an application login capability.
Persistence adapters own serialized login state. Existing framework rate limiting
is reused. Token claims are validated into a typed payload.
