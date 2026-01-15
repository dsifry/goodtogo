# Release

Create a new versioned release with changelog, updated documentation, and GitHub release.

## Usage

```
/project:release <major|minor|patch>
```

## Arguments

- `major` - Breaking changes (1.0.0 → 2.0.0)
- `minor` - New features, backwards compatible (0.58.0 → 0.59.0)
- `patch` - Bug fixes only (0.58.0 → 0.58.1)

## What This Does

### Phase 1: Gather Changes

1. Get current version from `package.json`
2. Find last release tag (e.g., `v0.58.0`)
3. Collect all commits since last tag:
   ```bash
   git log v0.58.0..HEAD --oneline --no-merges
   ```
4. Collect merged PRs since last tag:
   ```bash
   gh pr list --state merged --search "merged:>=$(git log -1 --format=%ci v0.58.0)" --json number,title,labels
   ```

### Phase 2: Calculate New Version

```bash
# Parse current version
CURRENT=$(cat package.json | jq -r .version)

# Calculate new version based on argument
case "$1" in
  major) NEW_VERSION=$(echo $CURRENT | awk -F. '{print $1+1".0.0"}') ;;
  minor) NEW_VERSION=$(echo $CURRENT | awk -F. '{print $1"."$2+1".0"}') ;;
  patch) NEW_VERSION=$(echo $CURRENT | awk -F. '{print $1"."$2"."$3+1}') ;;
esac
```

### Phase 3: Update Service Registry

```bash
# 1. Discover services from JSDoc
npx tsx scripts/verify-service-documentation.ts --output=data/service-audit.json

# 2. Sync service-registry.json
npx tsx scripts/sync-service-registry.ts --execute

# 3. Update SERVICE_INVENTORY.md from JSON
npx tsx scripts/update-service-inventory.ts
```

### Phase 4: Update CHANGELOG.md

Create or update `CHANGELOG.md` with format:

```markdown
# Changelog

## [v0.59.0] - 2026-01-10

### Features

- feat: Add DraftRecencyFilterStrategy to prevent duplicate drafts (#882)
- feat: BEADS multi-agent orchestration system (#881)

### Bug Fixes

- fix: Flatten nested AND clauses in ContactFilteringService (#882)

### Documentation

- docs: Add BEADS developer setup guide

### Other

- chore: Update service inventory
```

Group commits by conventional commit type:

- `feat:` → Features
- `fix:` → Bug Fixes
- `docs:` → Documentation
- `refactor:` → Refactoring
- `test:` → Testing
- `chore:` → Other

### Phase 5: Update package.json

```bash
# Update version in package.json
npm version $NEW_VERSION --no-git-tag-version
```

### Phase 6: Extract Learnings (REQUIRED)

Before cutting a release, extract strategic learnings from the conversation history. This ensures architectural decisions, debugging insights, and non-obvious behaviors discovered during the release cycle are captured.

```bash
# Extract conversation summaries from recent sessions
pnpm tsx scripts/conversation-history.ts summaries --recent 10

# Extract strategic dialogue for AI analysis
pnpm tsx scripts/conversation-history.ts extract --strategic-only --recent 5
```

Then invoke the extract-learnings command:

```
/project:extract-learnings --historical --recent 5
```

**This step is REQUIRED** - Release cycles often contain the richest architectural discussions and debugging insights that will be lost if not captured.

**Output**: Present candidate learnings to user for approval. Store approved learnings via `/project:til` workflow.

### Phase 7: Validate

```bash
# Run all checks
pnpm lint
pnpm typecheck
pnpm test --run
pnpm build
```

**IMPORTANT**: If any validation fails, STOP and fix issues before proceeding.

### Phase 8: Commit & Tag

```bash
# Stage all changes
git add package.json CHANGELOG.md docs/SERVICE_INVENTORY.md scripts/service-registry.json

# Commit
git commit -m "chore(release): v${NEW_VERSION}

- Updated changelog with all changes since v${PREV_VERSION}
- Updated service registry (${SERVICE_COUNT} services)
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
/project:release minor

> Current version: 0.58.0
> New version: 0.59.0
>
> Changes since v0.58.0:
> - 12 commits, 3 PRs merged
>
> Updating service registry...
> - Discovered 238 services (+2 new)
> - Updated scripts/service-registry.json
> - Updated docs/SERVICE_INVENTORY.md
>
> Updating CHANGELOG.md...
> - Added release notes for v0.59.0
>
> Running validation...
> ✓ Lint passed
> ✓ Typecheck passed
> ✓ Tests passed (287 tests)
> ✓ Build passed
>
> Creating release...
> ✓ Committed changes
> ✓ Created tag v0.59.0
> ✓ Pushed to origin
> ✓ Created GitHub release: https://github.com/dsifry/goodtogo/releases/tag/v0.59.0
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
