# Approved decision
The project selected a database-backed session revocation record checked by the existing SessionService on each authenticated operation. This replaces the previous stateless-only decision. Use the existing database transaction; add no queue or cache. Record the significant decision, link it from this change, then archive the change. Scope Delta: None.
