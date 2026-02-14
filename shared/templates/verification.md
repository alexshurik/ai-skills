# Verification Report: <Feature Name>

> Created by: Acceptance Reviewer
> Date: YYYY-MM-DD
> Proposal: ./proposal.md
> Design: ./design.md

## Summary

| Metric | Value |
|--------|-------|
| **Status** | ACCEPTED / NEEDS WORK |
| **Acceptance Criteria** | X/Y passed |
| **Test Coverage** | X% |
| **Tests** | X passed, 0 failed |

## Test Results

```
Test Suites: X passed, X total
Tests:       X passed, X total
Coverage:    X%
Time:        Xs
```

## Acceptance Criteria Verification

### AC-1: <Criterion from proposal.md>

| Aspect | Result |
|--------|--------|
| **Status** | PASS / FAIL |
| **Evidence** | <how verified> |
| **Test** | `<test file>:<test name>` |
| **Notes** | <observations> |

### AC-2: <Criterion from proposal.md>

| Aspect | Result |
|--------|--------|
| **Status** | PASS / FAIL |
| **Evidence** | <how verified> |
| **Test** | `<test file>:<test name>` |
| **Notes** | <observations> |

## Edge Cases

| Edge Case | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Empty input | <expected> | <actual> | PASS/FAIL |
| Invalid data | <expected> | <actual> | PASS/FAIL |
| Network failure | <expected> | <actual> | PASS/FAIL |
| Concurrent access | <expected> | <actual> | PASS/FAIL |

## E2E Flow Verification

### Flow: <Main User Flow>

| Step | Expected | Actual | Status |
|------|----------|--------|--------|
| 1. User initiates | <expected> | <actual> | PASS/FAIL |
| 2. System processes | <expected> | <actual> | PASS/FAIL |
| 3. Data persisted | <expected> | <actual> | PASS/FAIL |
| 4. User feedback | <expected> | <actual> | PASS/FAIL |

## Non-Functional Requirements

### Performance
- [ ] Response time < X ms
- [ ] Throughput > X req/s

### Security
- [ ] Authentication verified
- [ ] Authorization verified
- [ ] No sensitive data exposure

### Accessibility
- [ ] WCAG 2.1 AA compliance (if applicable)

## Issues Found

### Blocking Issues
<!-- Issues that must be fixed -->
None / List issues

### Non-Blocking Issues
<!-- Issues that can be fixed later -->
None / List issues

## Recommendations

<!-- Suggestions for future improvements -->
- <recommendation 1>
- <recommendation 2>

---

## Final Verdict

### ACCEPTED

All acceptance criteria from proposal.md have been verified. Tests are passing with adequate coverage. The implementation meets the requirements and is ready for deployment.

**OR**

### NEEDS WORK

The following issues must be addressed before acceptance:

1. **[Issue]**: <description>
   - **Impact**: <what's affected>
   - **Action**: <what to fix>

2. **[Issue]**: <description>
   - **Impact**: <what's affected>
   - **Action**: <what to fix>

---

## Sign-off

- **Reviewed by**: Acceptance Reviewer
- **Date**: YYYY-MM-DD
- **Next Steps**: <deployment / iteration>
