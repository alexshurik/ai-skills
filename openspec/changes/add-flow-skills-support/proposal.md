# Proposal: Add Flow Skill Support

## Vision

Currently, all feature development workflows require a manual orchestrator that controls each phase. While this provides flexibility, it also requires constant attention and decision-making between phases.

Flow skills provide **automated multi-agent workflows** that execute all phases without manual intervention, following a predefined diagram. This enables:
- Hands-off feature development for well-understood patterns
- Faster turnaround for standard tasks
- Consistent execution without human bottlenecks

## User Stories

**As a developer**, I want to run `/flow:sk-team-feature-flow "Add user authentication"` and have the system automatically:
1. Gather requirements via Product Analyst
2. Create design via Architect  
3. Write tests via Tester
4. Implement code via Developer
5. Review via Code Reviewer
6. Verify via Acceptance Reviewer

**As a tech lead**, I want automated quick fixes via `/flow:sk-team-quick-flow` that skip formal phases for bugs/typos.

**As a framework maintainer**, I want flow skills defined in `workflow/flows/` with Mermaid diagrams showing the execution path.

## Acceptance Criteria

### AC1: Flow Skill Format
- [ ] Flow skills use `type: flow` in YAML frontmatter
- [ ] Each flow skill contains a Mermaid diagram showing execution phases
- [ ] Diagram includes decision points and loops

### AC2: Directory Structure
- [ ] New directory `workflow/flows/` for flow skills
- [ ] Flow skills follow same naming: `sk-*-flow/`
- [ ] Separate from standard skills in `workflow/skills/`

### AC3: Flow Skills Created
- [ ] `sk-team-feature-flow` — full 6-phase automated workflow
- [ ] `sk-team-quick-flow` — streamlined 2-phase workflow
- [ ] Both include complete phase descriptions

### AC4: Installation Support
- [ ] `scripts/install-kimi.sh` installs flow skills
- [ ] Flow skills linked to `~/.config/agents/skills/`
- [ ] Works with `/flow:name` command

### AC5: Documentation
- [ ] `adapters/kimi/README.md` explains flow skills
- [ ] Clear distinction between `/skill:name` and `/flow:name`
- [ ] Usage examples for both

## Edge Cases

### EC1: Flow Failure Mid-Way
- Flow should report which phase failed
- Artifacts created up to failure point are preserved
- User can resume manually from failed phase

### EC2: Review Rejection Loop
- Code Reviewer may request changes
- Flow should support up to 3 iterations
- After 3 failures, escalate to user

### EC3: Acceptance Failure
- Acceptance Reviewer may find issues
- Flow should route back to appropriate phase:
  - Requirements issue → Product Analyst
  - Design issue → Architect
  - Implementation issue → Developer

## Definition of Done

- [ ] Both flow skills created and tested
- [ ] Installation script updated
- [ ] Documentation complete
- [ ] Can execute `/flow:sk-team-feature-flow` successfully
- [ ] Can execute `/flow:sk-team-quick-flow` successfully
