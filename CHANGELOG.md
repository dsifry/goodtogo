# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
