# GoodToMerge

**Deterministic PR readiness detection for AI coding agents**

GoodToMerge helps AI agents (like Claude Code) know exactly when a PR is ready to merge. No guessing, no polling indefinitely, no missing comments.

## The Problem

AI agents creating PRs face a common challenge: **How do I know when I'm actually done?**

- CI is still running... is it done yet?
- CodeRabbit left 12 comments... which ones need action?
- A reviewer requested changes... did I address them all?
- There are 3 unresolved threads... are they blocking?

Without deterministic answers, agents either wait too long, miss comments, or keep asking "is it ready yet?"

## The Solution

GoodToMerge provides **deterministic PR state analysis**:

- **✅ All CI checks passed** - No more polling, know exactly when CI completes
- **✅ All automated reviews done** - CodeRabbit, SonarQube, etc. have finished
- **✅ All actionable comments addressed** - Distinguishes "must fix" from "nice to have"
- **✅ All threads resolved** - Tracks conversation state across reviewers
- **✅ Ready to merge (or move on)** - Clear signal to proceed or wait for humans

## Who Is This For?

- **AI coding agents** (Claude Code, Cursor, Copilot Workspace) that create PRs
- **Developers** who want clear PR readiness signals
- **Teams** using automated code review tools (CodeRabbit, etc.)

## For AI Agents

If you're an AI agent setting up GoodToMerge for a project, here's what you need to do:

### Quick Setup (Copy to Any Project)

```bash
# 1. Clone GoodToMerge
git clone https://github.com/dsifry/goodtomerge.git /tmp/goodtomerge

# 2. Copy the .claude directory to your target project
cp -r /tmp/goodtomerge/.claude /path/to/your/project/

# 3. Install Beads (git-backed task management)
npm install -g @coderabbitai/beads

# 4. Initialize Beads in your project
cd /path/to/your/project
bd init --prefix yourproject
```

### Key Commands Once Installed

| Command | What It Does |
|---------|--------------|
| `/project:pr-shepherd <pr-number>` | Monitor PR until ready to merge |
| `/project:handle-pr-comments <pr-number>` | Address all review comments systematically |
| `/project:create-pr` | Create a comprehensive PR with proper description |
| `/project:start-task` | Assess and plan a new task |

### How PR Shepherd Works

```
1. Agent creates PR
2. Run: /project:pr-shepherd 123
3. PR Shepherd monitors:
   - CI/CD status (polls every 60s)
   - Automated review completion (CodeRabbit, etc.)
   - Comment threads (resolved vs unresolved)
   - Actionable vs non-actionable feedback
4. Agent receives clear signal:
   - "PR ready to merge" → proceed
   - "Waiting for human review" → move to other work
   - "Action required: 3 comments need fixes" → address them
```

### Configuration

Edit `CLAUDE.md` in your project with your specific:
- Build commands (`npm test`, `pytest`, `cargo test`, etc.)
- Lint commands (`eslint`, `ruff`, `clippy`, etc.)
- Any project-specific workflows

The skills and commands are language-neutral and adapt to your tooling.

## Quick Start

### Prerequisites

- [Claude Code CLI](https://claude.ai/code) installed
- Git repository
- Node.js (for Beads installation)

### Installation

#### 1. Clone GoodToMerge

```bash
git clone https://github.com/dsifry/goodtomerge.git
cd goodtomerge
```

#### 2. Install Superpowers (Required)

GoodToMerge includes the [Superpowers](https://github.com/obra/superpowers) plugin for sophisticated development workflows.

Superpowers is already included in `.claude/plugins/superpowers/` - no additional installation needed!

The plugin provides:
- **Test-Driven Development** - RED-GREEN-REFACTOR cycle
- **Systematic Debugging** - Root cause analysis
- **Brainstorming** - Design refinement before coding
- **Code Review** - Automated quality gates
- **Writing Plans** - Detailed implementation plans
- **Subagent Development** - Fast iteration with quality gates

See [Superpowers README](.claude/plugins/superpowers/README.md) for full documentation.

#### 3. Install Beads (Recommended)

[Beads](https://github.com/coderabbitai/beads) provides git-backed task management:

```bash
# Using pnpm (recommended)
pnpm add -g @coderabbitai/beads

# Using npm
npm install -g @coderabbitai/beads

# Verify installation
bd --version
```

See [Beads Setup Guide](docs/BEADS_SETUP.md) for complete installation and configuration.

#### 4. Setup for Your Project

Copy the `.claude/` directory to your project:

```bash
# In your project directory
cp -r /path/to/goodtomerge/.claude .

# Initialize beads
bd init

# Configure beads sync branch
bd config set sync.branch beads-sync
```

#### 5. Optional: Install Python CLI

GoodToMerge includes optional Python utilities:

```bash
# Install in development mode
pip install -e .

# Or use uv for faster installation
uv pip install -e .

# Verify
gtm --version
```

That's it! Claude Code will now use GoodToMerge workflows with Superpowers skills and Beads task management.

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
│   ├── commands/              # Slash commands for Claude Code (43 commands)
│   ├── guides/               # Git, workflow, session guides (9 guides)
│   └── plugins/
│       ├── goodtomerge/      # GoodToMerge-specific skills
│       │   └── skills/       # pr-shepherd, handling-pr-comments, beads, etc.
│       └── superpowers/      # Superpowers plugin (included)
│           └── skills/       # TDD, debugging, brainstorming, etc. (20 skills)
├── beads/
│   └── config.yaml.example   # Beads task management config
├── docs/
│   └── BEADS_SETUP.md        # Comprehensive Beads installation guide
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
- [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent - Sophisticated development workflows
- [Beads](https://github.com/coderabbitai/beads) by CodeRabbit - Git-backed task management
- Inspired by real-world PR workflows at scale

### Special Thanks

- **Jesse Vincent** ([obra](https://github.com/obra)) for the incredible Superpowers plugin
- **CodeRabbit team** for Beads task management system
- **Anthropic** for Claude Code and Claude AI

## Support

- **Issues**: [GitHub Issues](https://github.com/dsifry/goodtomerge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dsifry/goodtomerge/discussions)
- **Documentation**: See `.claude/` directory for detailed guides

---

**Made with Claude Code** 🤖
