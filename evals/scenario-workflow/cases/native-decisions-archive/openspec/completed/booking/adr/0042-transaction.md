# ADR 0042: One database transaction
Status: Accepted

## Context
Stock and booking records must agree.

## Decision
Use one database transaction for stock and reservation updates.

## Consequences
The service owns commit and rollback.
