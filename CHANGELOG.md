# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.10.0] - 2026-02-18

### Features

- feat: Add Vercel deployment bot support (#37)
  - New VercelParser classifies all Vercel bot comments as NON_ACTIONABLE
  - Prevents false ACTION_REQUIRED status from deployment notifications
  - Author detection: `vercel[bot]`
  - Fallback body signature detection: `[vc]:`, `vercel.com`, `.vercel.app` URLs

## [0.9.0] - 2026-02-09

### Documentation

- docs: Add MC/DC (Modified Condition/Decision Coverage) testing methodology to workflow infrastructure (#36)
  - New MC/DC section in testing-patterns.md with decision tables and baseline+toggle pattern
  - Test automator agent updated with Step 2b Decision Table Analysis
  - Code review agent rubric extended with MC/DC evaluation criteria
  - Fixed `as any` contradiction in test-automator examples (replaced with `// @ts-expect-error`)
  - Aligned decision table condition names with explicit boolean expressions

## [0.8.1] - 2026-01-27

### Documentation

- docs: Add agent customization guide to USAGE.md (adding, modifying, file format)
- docs: Add agent workflows and orchestration guide to USAGE.md (phases, dependencies, custom workflows)

## [0.8.0] - 2026-01-20

### Features

- feat: Add `/rerun-gtg` comment trigger for quick merge-readiness checks (#33)
- feat: Add GTG Re-run workflow with dual triggers (comment + manual dispatch)
- feat: Add emoji reactions for comment-triggered runs (👀 → 🚀/😕)
- feat: Add exit code 1 special handling (allow merge if threads resolved)

### Bug Fixes

- fix: Use exact check names in --exclude-checks (gtg uses exact matching)

### Documentation

- docs: Clarify --exclude-checks uses exact name matching
- docs: Add GTG Re-run workflow documentation with full examples
- docs: Add PR shepherd integration guide with Python examples
- docs: Expand AI agent setup checklist to 7 steps
- docs: Standardize on GITHUB_TOKEN in workflow examples (PAT optional for private repos)
- docs: Replace static coverage badge with dynamic CI status badge

## [0.7.5] - 2026-01-19

### Documentation

- docs: Expand GitHub Actions integration with AI agent instructions
- docs: Add dual trigger pattern (pull_request + pull_request_review)
- docs: Add workflow_run pattern for complex CI pipelines
- docs: Add manual re-run workflow for quick GTG checks
- docs: Add Complete Setup Checklist for AI agents
- docs: Update Branch Protection section with new job names

## [0.7.4] - 2026-01-17

### Documentation

- docs: Fix status value from UNRESOLVED_THREADS to UNRESOLVED in all docs
- docs: Add missing ERROR status to status tables

## [0.7.3] - 2026-01-17

### Documentation

- docs: Fix USAGE.md to show --repo as optional (auto-detects from git origin)
- docs: Add missing --exclude-checks option to CLI reference
- docs: Fix cache location from ~/.goodtogo to .goodtogo (project-local)
- docs: Fix cache bypass flag from --no-cache to --cache none
- docs: Update parser descriptions for Claude, Cursor, Greptile accuracy
- docs: Update CONTRIBUTING.md parser example to use Template Method pattern
- docs: Add agent_state.py and time_provider.py to architecture diagram

## [0.7.2] - 2026-01-17

### Documentation

- docs: Make release command language-agnostic with multi-language support
- docs: Add semantic versioning rules table mapping commit prefixes to version bumps
- docs: Add version bump validation to warn on mismatched commit types

## [0.7.1] - 2026-01-17

### Bug Fixes

- fix: Sync __version__ variable with package metadata

## [0.7.0] - 2026-01-17

### Features

- feat: Use template method pattern to handle resolved threads in all parsers
- feat: Classify PR summary comments as NON_ACTIONABLE

### Bug Fixes

- fix: Map comment database IDs to thread resolution status

This release fixes a critical bug where resolved threads were still being classified
as actionable. The fix ensures that all parsers respect GitHub's thread resolution
status, and adds patterns to recognize PR-level summary comments from Claude and
Cursor as non-actionable.

## [0.6.0] - 2026-01-17

### Features

- feat: Add GitHub Pages landing page with philosophy and vision
- feat: Enhanced README with badges, mermaid diagram, and better narrative

### Documentation

- docs: Create comprehensive landing page at dsifry.github.io/goodtogo
- docs: Add architecture diagram showing PR analysis flow
- docs: Improve quick start and usage examples

## [0.5.0] - 2026-01-17

### Features

- feat: Add state persistence to CLI for classification caching (#24)
- feat: Parse 'Outside diff range' comments from CodeRabbit (#31)
- feat: Add review timestamps for new review detection (#32)

### Bug Fixes

- fix: Improve parser recognition for Claude and Greptile bots (#25)

### Documentation

- docs: Add agent workflow data needs investigation (#30)

## [0.4.0] - 2026-01-17

### Features

- feat: Add classification persistence for dismissed comments (#23)
- feat: Add deterministic PR-level summary comment detection (#22)
- feat: Auto-detect repository from git origin (#21)
- feat: Add AI-friendly exit codes as default (#19)
- feat: Add --exclude-checks option to prevent circular CI dependency (#18)
- feat: Add state persistence for agent workflow tracking (#17)
- feat: Reduce AMBIGUOUS classification rate in parsers (#16)
- feat: Add URL field to Comment model for agent workflows (#12)
- feat: Add thread resolution data for agent workflows (#11)

### Bug Fixes

- fix: Invalidate cache for non-READY PR status (#29)
- fix: Correct PyPI package name from goodtogo to gtg (#15)
- fix: gtg-check workflow race condition (#3)

### Documentation

- docs: Add knowledge base with learnings from PR reviews (#27)
- docs: Add GitHub Actions and branch protection documentation (#26)
- docs: Update gtg command syntax and exit code documentation (#20)
- docs: Add real example output and fix CLI syntax (#14)

### Other

- chore: Add Claude Code GitHub Workflow (#1)

## [0.3.0] - 2026-01-16

### Features

- Initial public release with core PR analysis functionality
- CodeRabbit, Greptile, Claude Code, and Cursor parser support
- CI status aggregation and thread resolution tracking
- JSON and text output formats
- Semantic exit codes for shell scripting

## [0.2.0] - 2026-01-15

### Features

- Added comment classification system (ACTIONABLE, NON_ACTIONABLE, AMBIGUOUS)
- Parser framework for automated reviewer detection
- Basic caching for API responses

## [0.1.0] - 2026-01-15

### Features

- Initial development release
- Basic GitHub API integration
- PR status fetching and analysis
