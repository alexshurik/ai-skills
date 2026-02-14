# Cursor Adapter

## Installation

Generate `.cursorrules` file:

```bash
./scripts/generate-cursorrules.sh
```

Then copy to your project:

```bash
cp adapters/cursor/.cursorrules /path/to/your/project/
```

## Usage

After adding `.cursorrules` to your project, Cursor will have context about available commands:

```
/sk-team-help       # Team workflow documentation
/sk-team-feature    # Full feature development
/sk-team-quick      # Quick fix workflow
/sk-onboard         # Project onboarding
```

## How It Works

Cursor reads `.cursorrules` from your project root. The generated file contains:

1. **Command descriptions** - What each `/sk-*` command does
2. **Agent definitions** - Available agents and their roles
3. **Usage examples** - How to invoke commands

## Customization

Edit `.cursorrules` after generation to:
- Add project-specific rules
- Remove unused commands
- Add custom instructions

## Template

A `.cursorrules.template` is provided for reference:

```
# Project Rules

## Available Commands

### /sk-team-feature
Start full feature development with multi-agent team.

### /sk-team-quick
Quick fix workflow for bugfixes and small changes.

...
```

## Limitations

- Cursor doesn't have built-in skill/agent system like Claude Code
- Commands are documentation only - you manually invoke them in chat
- No automatic tool restrictions
