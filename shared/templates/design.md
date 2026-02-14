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

## Dependencies

### New Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| <package> | <version> | <why> |

### External Services
<!-- Any new integrations -->

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

## Implementation Notes
<!-- Any notes for developers -->
