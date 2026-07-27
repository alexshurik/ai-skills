# Project rules

- HTTP handlers map transport input, call one application capability, and map the
  result to a response.
- The application layer owns business policy.
- Persistence adapters own store keys, serialization, expiry, and atomic updates.
- Framework integrations belong to the framework/infrastructure layer.
- External token claims must be validated into an explicit type before application
  policy consumes them.
