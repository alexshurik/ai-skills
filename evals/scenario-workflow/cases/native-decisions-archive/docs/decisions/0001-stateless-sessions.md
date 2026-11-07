# ADR 0001: Stateless sessions
Status: Accepted

## Context
The first release needed a small authentication surface.

## Decision
Use signed stateless session tokens.

## Alternatives
A persistent session registry.

## Consequences
Tokens remain valid until expiry.
