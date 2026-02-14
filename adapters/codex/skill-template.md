# Codex Skill Template

Use this template when creating new skills compatible with OpenAI Codex.

## Format

```yaml
---
name: sk-example
version: 1.0.0
description: Brief description of what this skill does
license: MIT

# Tools this skill needs
allowed-tools: Read, Write, Bash, Glob, Grep

# Cross-platform compatibility
platforms:
  codex: true
  cursor: true
  kimi: true
---

# /sk-example - Skill Title

<sk-example>

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

</sk-example>
```

## Best Practices

1. **Use XML tags** - Wrap main content in `<skill-name>` tags
2. **Clear steps** - Number your steps clearly
3. **Include examples** - Show command examples
4. **Define guardrails** - State what the skill should NOT do
5. **Keep it focused** - One skill = one purpose

## Testing

Test your skill by:

1. Copy to skills directory
2. Restart the agent
3. Invoke with `/sk-example`
4. Verify behavior matches expectations
