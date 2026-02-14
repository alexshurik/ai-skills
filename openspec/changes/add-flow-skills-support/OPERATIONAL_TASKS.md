# Operational Tasks: Add Flow Skill Support

## Pre-Deployment (Required)

### Installation

All developers should reinstall skills to get flow support:

```bash
cd /path/to/skills-repo
./scripts/install-kimi.sh
```

**Verify installation:**
```bash
ls ~/.config/agents/skills/ | grep flow
# Should show: sk-team-feature-flow, sk-team-quick-flow
```

### Environment Setup

No new environment variables required for flow skills.

## Post-Deployment (Required)

### Team Communication

- [ ] Announce new `/flow:` commands in team chat
- [ ] Share examples:
  ```
  /flow:sk-team-feature-flow Add user authentication with Google OAuth
  /flow:sk-team-quick-flow Fix null pointer in user service
  ```
- [ ] Update team wiki with new workflow options

### Training

- [ ] Explain difference between `/skill:` and `/flow:`
  - `/skill` = Manual orchestration (flexible)
  - `/flow` = Automated execution (hands-off)
- [ ] When to use which:
  - Complex features → `/skill:sk-team-feature`
  - Standard patterns → `/flow:sk-team-feature-flow`
  - Quick fixes → `/flow:sk-team-quick-flow`

### Documentation Review

- [ ] Review `adapters/kimi/README.md` with team
- [ ] Ensure everyone understands new artifact types:
  - SUMMARY.md for stakeholders
  - API_CHANGELOG.md for frontend
  - OPERATIONAL_TASKS.md for ops

## Monitoring

No specific monitoring needed for this framework feature.

## Rollback Plan

If issues arise:
1. Skills can be uninstalled: `./scripts/uninstall.sh`
2. Previous `/skill:` commands continue to work
3. No database or infrastructure changes involved

## Contacts

- Framework maintainer: Check `AGENTS.md` in skills repo
- Kimi CLI docs: https://moonshotai.github.io/kimi-cli/

---

**Note**: This is a low-risk framework update. No production infrastructure changes required.
