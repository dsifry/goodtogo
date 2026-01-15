# GoodToMerge

**Language-neutral Claude Code workflow system for PR excellence**

GoodToMerge is a comprehensive workflow system for [Claude Code](https://claude.ai/code) that helps you achieve PR excellence through sophisticated automation, task management, and code quality workflows.

## What is GoodToMerge?

GoodToMerge provides:

- **🤖 Sophisticated PR Workflows** - Auto-shepherd PRs from creation to merge
- **📋 Task Management** - Beads-based issue tracking integrated with Claude Code
- **🔍 Code Quality** - Automated reviews, testing, and validation
- **🌍 Language-Neutral** - Works with any codebase (Python, Rust, TypeScript, Go, etc.)
- **🎯 Simple & Concise** - Clear workflows without overwhelming complexity

## Quick Start

### Prerequisites

- [Claude Code CLI](https://claude.ai/code) installed
- Git repository
- [Beads](https://github.com/coderabbitai/beads) for task management (optional but recommended)

### Installation

```bash
# Clone this repository
git clone https://github.com/dsifry/goodtomerge.git
cd goodtomerge

# Install Python dependencies (optional - for gtm CLI)
pip install -e .

# Or use uv for faster installation
uv pip install -e .
```

### Setup for Your Project

Copy the `.claude/` directory to your project:

```bash
# In your project directory
cp -r /path/to/goodtomerge/.claude .

# Initialize beads (optional)
bd init
```

That's it! Claude Code will now use GoodToMerge workflows.

## Core Features

### PR Shepherd

Automatically monitors PRs through to merge:

```
/project:pr-shepherd [pr-number]
```

- Watches CI/CD status
- Handles review comments systematically
- Auto-fixes common issues
- Resolves conversation threads
- Notifies when ready to merge

### Handle PR Comments

Systematic response to code review feedback:

```
/project:handle-pr-comments <pr-number>
```

- Reads all review threads
- Groups by file and concern
- Implements fixes with proper attribution
- Marks conversations resolved

### Task Management with Beads

Track work across sessions:

```bash
# Create task
bd create --title="Add user auth" --type=feature

# List ready work
bd ready

# Update status
bd update <id> --status=in_progress

# Close when done
bd close <id>
```

See [Beads Workflow Guide](.claude/plugins/goodtomerge/skills/beads/SKILL.md) for details.

### Session Management

Save and resume work context:

```
/project:save-session my-feature-work
/project:load-session my-feature-work
/project:list-sessions
```

### Worktree Development

Parallel development workflows:

```
/project:worktree-create my-feature feat/my-feature
/project:worktree-status
/project:peek-branch main src/app.py
```

## Available Commands

All commands are in `.claude/commands/`:

| Command | Purpose |
|---------|---------|
| `/project:pr-shepherd` | Monitor PR to merge |
| `/project:handle-pr-comments` | Address review feedback |
| `/project:create-pr` | Create comprehensive PR |
| `/project:create-issue` | Create GitHub issue with agent instructions |
| `/project:start-task` | Task assessment and planning |
| `/project:review-this` | CTO-level spec/plan review |
| `/project:production-mode` | Safety protocol for production systems |
| `/project:save-session` | Save conversation context |
| `/project:load-session` | Resume previous session |
| `/project:worktree-create` | Create parallel workspace |

See [Commands Directory](.claude/commands/) for all available commands.

## Project Structure

```
goodtomerge/
├── .claude/
│   ├── commands/              # Slash commands for Claude Code
│   ├── guides/               # Git, workflow, session guides
│   └── plugins/goodtomerge/
│       └── skills/           # Auto-activating skills
├── beads/
│   └── config.yaml.example   # Beads task management config
├── src/goodtomerge/          # Python utilities (optional)
│   ├── cli.py               # CLI tools
│   └── __init__.py
└── pyproject.toml           # Python package config
```

## Language-Neutral Design

GoodToMerge works with **any** programming language:

- Git/PR workflows are universal
- No language-specific assumptions in commands
- Skills adapt to your project's tools
- Task management is project-agnostic

Example usage:
- **Python**: `pytest`, `ruff`, `mypy`
- **Rust**: `cargo test`, `cargo clippy`
- **TypeScript**: `pnpm test`, `eslint`
- **Go**: `go test`, `golangci-lint`

Just update `CLAUDE.md` in your project with your specific build/test commands.

## Customization

### Adapt to Your Project

1. Copy `.claude/` to your project
2. Edit `CLAUDE.md` with your:
   - Build commands
   - Test commands
   - Linting/formatting tools
   - Project-specific workflows
3. Update skill references if needed

### Add Custom Skills

Create new skills in `.claude/plugins/goodtomerge/skills/`:

```markdown
---
name: my-custom-skill
description: Does something awesome
---

# Skill content here
```

Skills auto-activate based on context.

## Philosophy

GoodToMerge follows these principles:

1. **Language-Neutral** - Works everywhere
2. **Simple & Concise** - Clear over clever
3. **Sophisticated Workflows** - Proven patterns
4. **Task Persistence** - Beads for multi-session work
5. **Community-Driven** - Open source and extensible

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a PR

Use GoodToMerge's own workflows for development:

```bash
/project:start-task "Add new feature"
# ... do work ...
/project:create-pr
/project:pr-shepherd
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Created by [David Sifry](https://github.com/dsifry) with ❤️ for the Claude Code community.

Built on:
- [Claude Code](https://claude.ai/code) by Anthropic
- [Beads](https://github.com/coderabbitai/beads) for task management
- Inspired by real-world PR workflows at scale

## Support

- **Issues**: [GitHub Issues](https://github.com/dsifry/goodtomerge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dsifry/goodtomerge/discussions)
- **Documentation**: See `.claude/` directory for detailed guides

---

**Made with Claude Code** 🤖
