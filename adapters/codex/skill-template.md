# Codex Skill Template

Use this template when creating new skills compatible with OpenAI Codex.

## Format

```yaml
---
name: sk-example
description: Explain when Codex should and should not use this skill.
---

# Skill Title

## Purpose

What this skill does and when to use it.

## Process

### Step 1: First Action

Description of first step.

```bash
# Example command
ls -la
```

### Step 2: Second Action

Description of second step.

### Step 3: Output

What to produce at the end.

## Guardrails

- What NOT to do
- Constraints to follow

```

## Best Practices

1. **Write a precise description** - Include triggers and important exclusions
2. **Clear steps** - Number your steps clearly
3. **Include examples** - Show command examples
4. **Define guardrails** - State what the skill should not do
5. **Keep it focused** - One skill, one purpose
6. **Use `agents/openai.yaml` when needed** - Put UI metadata, invocation policy,
   and declared tool dependencies there

## Testing

Test your skill by:

1. Add the skill source to `skills-manifest.yaml`
2. Run `scripts/validate-skills.sh`
3. Run `scripts/install-codex.sh`
4. Invoke with `$sk-example` or select it through `/skills`
5. Verify explicit and implicit behavior
