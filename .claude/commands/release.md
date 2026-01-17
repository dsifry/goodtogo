# Release

Create a new versioned release with changelog, updated documentation, and GitHub release.

## Usage

```
/project:release <major|minor|patch>
```

## Arguments

- `major` - Breaking changes (1.0.0 → 2.0.0)
- `minor` - New features, backwards compatible (0.58.0 → 0.59.0)
- `patch` - Bug fixes, documentation, refactoring (0.58.0 → 0.58.1)

## Semantic Versioning Rules

**CRITICAL**: Use conventional commit prefixes to determine version type:

| Commit Prefix | Version Bump | Examples |
|---------------|--------------|----------|
| `feat:` | **minor** | New functionality, new API endpoints |
| `fix:` | patch | Bug fixes, error corrections |
| `docs:` | patch | README, comments, documentation |
| `refactor:` | patch | Code restructuring, no behavior change |
| `test:` | patch | Adding/updating tests |
| `chore:` | patch | Build, CI, dependencies |
| `perf:` | patch (or minor if significant) | Performance improvements |
| `BREAKING CHANGE:` | **major** | Any breaking API change |

**Common mistakes to avoid:**
- Using `feat:` for documentation changes (use `docs:`)
- Bumping minor version for non-feature changes
- Releasing with no actual code changes

## What This Does

### Phase 1: Detect Project Type

Auto-detect project type from configuration files:

| File | Language | Version Location |
|------|----------|------------------|
| `pyproject.toml` | Python | `[project] version = "X.Y.Z"` |
| `package.json` | Node.js | `"version": "X.Y.Z"` |
| `Cargo.toml` | Rust | `version = "X.Y.Z"` |
| `go.mod` | Go | Use git tags only |
| `*.gemspec` | Ruby | `version = "X.Y.Z"` |
| `pom.xml` | Java/Maven | `<version>X.Y.Z</version>` |
| `build.gradle` | Gradle | `version = 'X.Y.Z'` |

If project uses `src/<package>/__init__.py` with `__version__`, update that too.

### Phase 2: Gather Changes

1. Get current version from detected config file
2. Find last release tag (e.g., `v0.5.0`)
3. Collect all commits since last tag:
   ```bash
   git log v0.5.0..HEAD --oneline --no-merges
   ```
4. Collect merged PRs since last tag:
   ```bash
   gh pr list --state merged --search "merged:>=$(git log -1 --format=%ci v0.5.0)" --json number,title,labels
   ```

### Phase 3: Validate Version Bump

**BEFORE calculating new version**, analyze commits to verify correct bump type:

1. List all commits since last tag
2. Categorize by conventional commit prefix
3. If user requested `minor` but no `feat:` commits exist, WARN and suggest `patch`
4. If user requested `patch` but `feat:` commits exist, WARN and suggest `minor`
5. If any commit has `BREAKING CHANGE:`, require `major`

```
Example validation output:
> Commits since v0.5.0:
>   docs: Add GitHub Pages landing page (1 commit)
>   docs: Enhanced README (1 commit)
>
> ⚠️  WARNING: You requested 'minor' but found 0 feat: commits.
>     All commits are documentation changes.
>     Recommended: 'patch' → v0.5.1
>     Continue with 'minor' anyway? [y/N]
```

### Phase 4: Calculate New Version

Parse version from detected config file and increment appropriately.

### Phase 5: Update CHANGELOG.md

Create or update `CHANGELOG.md` with format:

```markdown
# Changelog

## [v0.6.0] - 2026-01-10

### Features

- feat: Add DraftRecencyFilterStrategy to prevent duplicate drafts (#882)

### Bug Fixes

- fix: Flatten nested AND clauses in ContactFilteringService (#882)

### Documentation

- docs: Add developer setup guide

### Other

- chore: Update dependencies
```

Group commits by conventional commit type:

- `feat:` → Features
- `fix:` → Bug Fixes
- `docs:` → Documentation
- `refactor:` → Refactoring
- `test:` → Testing
- `chore:` → Other

### Phase 6: Update Version Files

Update version in ALL relevant locations based on detected project type:

**Python (`pyproject.toml`):**
```toml
[project]
version = "X.Y.Z"
```
Also update `src/<package>/__init__.py` if it contains `__version__`.

**Node.js (`package.json`):**
```bash
npm version $NEW_VERSION --no-git-tag-version
```

**Rust (`Cargo.toml`):**
```toml
version = "X.Y.Z"
```

**Go:** Use git tags only (no version file).

**Ruby (`*.gemspec`):**
```ruby
spec.version = "X.Y.Z"
```

### Phase 7: Validate

Run project validation commands. Reference CLAUDE.md for project-specific commands:

```bash
# Generic pattern - adapt to project
<TEST_COMMAND>      # e.g., pytest, npm test, cargo test, go test
<LINT_COMMAND>      # e.g., ruff check, eslint, clippy
<TYPECHECK_COMMAND> # e.g., mypy, tsc --noEmit
<BUILD_COMMAND>     # e.g., pip install -e ., npm run build, cargo build
```

**For this project (Python):**
```bash
pytest && ruff check . && black --check . && mypy src/
```

**IMPORTANT**: If any validation fails, STOP and fix issues before proceeding.

### Phase 8: Commit & Tag

Stage files based on detected project type:

```bash
# Stage version files (adapt to project type)
# Python: pyproject.toml, src/<package>/__init__.py
# Node.js: package.json, package-lock.json
# Rust: Cargo.toml, Cargo.lock
# Always: CHANGELOG.md

git add <VERSION_FILES> CHANGELOG.md

# Commit
git commit -m "chore(release): v${NEW_VERSION}

- Updated changelog with all changes since v${PREV_VERSION}
- Bumped version to ${NEW_VERSION}

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Create annotated tag
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"
```

### Phase 9: Push & Create GitHub Release

```bash
# Push commit and tag
git push origin main
git push origin "v${NEW_VERSION}"

# Create GitHub release with auto-generated notes
gh release create "v${NEW_VERSION}" \
  --title "v${NEW_VERSION}" \
  --notes-file CHANGELOG_CURRENT.md \
  --latest
```

Where `CHANGELOG_CURRENT.md` contains just the current release notes section.

## Example

```
/project:release patch

> Detected project type: Python (pyproject.toml)
> Current version: 0.5.0
>
> Commits since v0.5.0:
>   docs: Add GitHub Pages landing page (1)
>   docs: Enhanced README with badges (1)
>
> ⚠️  Analysis: Found 0 feat: commits, 2 docs: commits
>    Requested: patch ✓ (correct for docs-only changes)
>
> New version: 0.5.1
>
> Updating CHANGELOG.md...
> - Added release notes for v0.5.1
>
> Updating version files...
> - pyproject.toml: 0.5.0 → 0.5.1
> - src/goodtogo/__init__.py: 0.5.0 → 0.5.1
>
> Running validation...
> ✓ pytest passed (45 tests)
> ✓ ruff check passed
> ✓ black --check passed
> ✓ mypy passed
>
> Creating release...
> ✓ Committed changes
> ✓ Created tag v0.5.1
> ✓ Pushed to origin
> ✓ Created GitHub release
```

## Rollback

If something goes wrong after tagging but before pushing:

```bash
git tag -d v${NEW_VERSION}
git reset --hard HEAD~1
```

If already pushed:

```bash
# Delete remote tag
git push origin :refs/tags/v${NEW_VERSION}

# Delete GitHub release
gh release delete v${NEW_VERSION} --yes

# Revert commit
git revert HEAD
git push
```

## Notes

- Always run on `main` branch
- Ensure working directory is clean before starting
- All tests must pass before release
- The release skill will ask for confirmation before pushing
