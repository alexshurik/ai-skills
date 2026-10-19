# Review-enforcement regression corpus

This corpus turns observed workflow failures into stable review decisions. It is
designed for fresh-context model evals and for deterministic contract tests around
the collector and approval gate.

The cases cover:

- Deli Check's module-level FastAPI handlers beside the router's existing CBV;
- Spotty's final-review snapshot differing from the committed source;
- missing lens artifacts;
- Radon/Lizard/jscpd findings emitted with exit code zero;
- undispositioned module-growth leads, incomplete OpenSpec tasks, and large scope;
- negative controls for a cohesive large file, a non-route pure helper, and an
  authority-approved multiple-owner route design.

`cases.json` contains only scenarios. `goldens.json` is the held-out answer key.
Run `python3 validate.py` after editing the corpus. A live harness should provide
the current review skill/policies plus one scenario and score the structured answer
against the matching golden without exposing `goldens.json` to the model.
