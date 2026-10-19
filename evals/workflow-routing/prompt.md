# Adaptive workflow routing decision

Read every file listed in `policy-inputs.txt`, then evaluate the supplied scenario
under those policies. Treat the scenario as the complete user and workflow state
for one objective. Do not search outside the fixture for eval configuration,
answer keys, other cases, or previous responses.

Return only the JSON object required by `response.schema.json`.

Decision rules for this eval:

- Report the route, assurance, and other charter values that govern the next valid
  action. If a route must escalate, report the resulting route and the upward
  transition.
- If one charter choice is unresolved, report the recommendation that belongs in
  the single compact charter and select `ask_compact_charter`.
- `approval` describes the immediate next control action for the stated phase, not
  a generic summary of the authorization mode.
- `agent_shape` describes the authorized topology for the resulting route or the
  narrower remediation wave. Use `blocked_before_dispatch` when a user-owned
  decision must occur before more agents can start.
- `broad_suite` describes what should happen to the broad applicable test receipt
  at this point. Do not turn an exact-input reuse decision into a rerun.
- Use a typed stop only for a policy boundary that requires the user. An ordinary
  return to implementation is not a typed stop.
- Decide from behavior and authority. Do not add explanations, quotes, or prose.
