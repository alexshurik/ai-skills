# Technical Design: <Feature Name>

> Created by: Architect
> Date: YYYY-MM-DD
> Status: Draft | Ready for Implementation
> Proposal: ./proposal.md

## Overview

### Summary
<!-- High-level description of the technical approach -->

### Key Decisions
<!-- Important architectural decisions and rationale -->

| Decision | Choice | Rationale |
|----------|--------|-----------|
| <decision> | <choice> | <why> |

## Scope Delta

### Required by the Request
- <requirement or acceptance-criterion IDs>

### Approved Additions
| ID | Addition | Approval source | Cost/blast radius |
|---|---|---|---|
| None | | | |

### Explicit Non-Goals
- <item>

Unselected proposals belong in `DEFERRED.md`, not this normative design.

## Authority and Constraints

| ID / Source | Authority | Applicable decisions |
|---|---|---|
| <C-* or artifact> | User / approved artifact / repository policy | <constraint> |

Do not promote caller assumptions or implementation preferences into constraints.

## Architecture

### Component Diagram
```
┌─────────────┐     ┌─────────────┐
│ Component A │────►│ Component B │
└─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│ Component C │
└─────────────┘
```

### New Components

#### <Component Name>
- **Responsibility**: <what it does>
- **Interface**: <public API>
- **Dependencies**: <what it needs>

### Modified Components

#### <Existing Component>
- **Current**: <current behavior>
- **Change**: <what changes>
- **Reason**: <why>

### Boundary Ownership

| Concern | Input/trust boundary | Primary owner | Boundary model | Forbidden locations |
|---|---|---|---|---|
| <concern> | <input> | <owner> | <model> | <locations> |

## Data Flow

### Sequence Diagram
```
User ──► Frontend ──► API ──► Service ──► Database
                                  │
                                  ▼
                              External API
```

### Flow Description
1. <step 1>
2. <step 2>
3. <step 3>

### Trust Boundaries

| Input | Validation/conversion owner | Precise model | Consumer |
|---|---|---|---|
| <external or serialized input> | <owner> | <model> | <component> |

## API Design

### New Endpoints

#### `POST /api/<resource>`
- **Description**: <what it does>
- **Request**:
  ```json
  {
    "field": "type"
  }
  ```
- **Response**:
  ```json
  {
    "field": "type"
  }
  ```
- **Errors**: <error cases>

### Modified Endpoints
<!-- List changes to existing endpoints -->

## Data Model Changes

### Schema Changes
```sql
-- New table
CREATE TABLE <table_name> (
  id UUID PRIMARY KEY,
  ...
);

-- Modified table
ALTER TABLE <table_name> ADD COLUMN ...;
```

### Migrations
<!-- Migration strategy -->

### State and Coordination Alignment

Use only when durable state or concurrency changes.

| Invariant | Protected resource/operation | Source of truth and scope | Transaction/coordination scope | Lifecycle, deletion, retry, and recovery owner |
|---|---|---|---|---|
| <invariant> | <resource> | <state owner/scope> | <coordination scope> | <owner and behavior> |

## Dependencies

### New Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| <package> | <version> | <why> |

### External Services
<!-- Any new integrations -->

## Abstraction and Mechanism Decisions

### Abstraction Budget

| Abstraction | Current consumers | Independently testable responsibility | Keep / inline |
|---|---:|---|---|
| <item> | <count> | <responsibility> | <decision> |

### Mechanism Budget

Use only when an operational mechanism is added or materially changed.

| Mechanism | Invariant served | Simplest viable alternative | Permanent complexity | Boundedness/lifecycle | Keep / remove |
|---|---|---|---|---|---|
| <mechanism> | <invariant> | <alternative> | <recurring cost/failures> | <bounds> | <decision> |

## Module Growth

| File | Current lines | Responsibility before | Responsibility added | Split / keep rationale |
|---|---:|---|---|---|
| <path> | <count> | <before> | <added> | <decision> |

## Infrastructure Authority and Non-Goals

- **Authorized runtime/deployment/configuration/observability scope:** <scope>
- **Owner:** <owner>
- **Explicitly unchanged adjacent systems/contracts:** <non-goals>

## Security Considerations

### Authentication
<!-- How auth is handled -->

### Authorization
<!-- Permission model -->

### Data Protection
<!-- Sensitive data handling -->

## Performance Considerations

### Caching Strategy
<!-- What to cache, where, TTL -->

### Optimization
<!-- Performance optimizations -->

### Scalability
<!-- How it scales -->

## Error Handling

### Error Types
| Error | Code | Handling |
|-------|------|----------|
| <error> | <code> | <how to handle> |

### Recovery
<!-- Recovery strategies -->

## Testing Strategy

### Unit Tests
<!-- What to unit test -->

### Integration Tests
<!-- What to integration test -->

### E2E Tests
<!-- What to E2E test -->

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| <risk> | High/Med/Low | High/Med/Low | <mitigation> |

## Structural Digest

- **Architecture summary:** <summary>
- **File map:** <NEW/MODIFIED paths and owners>
- **Model/public-interface changes:** <changes or none>
- **Task dependencies:** <summary>
- **Risks and non-goals:** <summary>
- **Required ADRs:** <paths or none>

## Implementation Notes
<!-- Any notes for developers -->
