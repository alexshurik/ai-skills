# Remediation-routing forward evaluation

Read the supplied skill inputs and one case input. Do not read or infer the case's
expected result. Return only:

```text
Required outcome: ...
Constraint audit: traceable constraint | non-binding preference | none
Remedy authority: within_approved_design | architecture_decision_required |
  scope_decision_required | investigation_required
Route: Developer | Architecture | Scope Triage | Investigation
Why: ...
Forbidden next action: ...
```

Judge whether the outcome is mandatory separately from who may choose its remedy.
Do not design or implement the fix.
