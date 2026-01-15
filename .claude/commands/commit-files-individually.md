---
model: claude-haiku-4-5-20251001
---

# /project:commit-files-individually

Stage and commit all modified files one by one with intelligent commit messages.

## Usage

```
/project:commit-files-individually
```

## Overview

This command systematically processes all modified files in the repository, staging and committing them individually with descriptive commit messages. It's particularly useful for large changesets where you want granular commit history.

## Process

1. **File Discovery**: Lists all modified files using `git status --porcelain`
2. **File Analysis**: For each file, analyzes the changes using `git diff`
3. **Message Generation**: Creates appropriate commit messages based on:
   - File type and location
   - Nature of changes (formatting, functionality, documentation)
   - Content analysis for context
4. **Individual Commits**: Stages and commits each file separately
5. **Progress Tracking**: Shows progress through the file list

## Implementation

The command will:

### 1. Analyze File Changes

```bash
# Get all modified files
MODIFIED_FILES=$(git status --porcelain | grep "^ M" | cut -c4-)

# For each file, check what changed
git diff "$file" | head -20  # Sample changes for analysis
```

### 2. Categorize Changes

Based on file patterns and diff content:

- **Documentation**: `*.md` files → "docs: ..."
- **Configuration**: `*.json`, `*.js` config files → "config: ..."
- **Tests**: `*.test.ts`, `__tests__/` → "test: ..."
- **Source Code**: `src/` files → "feat:", "fix:", "refactor:"
- **Scripts**: `scripts/` → "scripts: ..."
- **Claude Files**: `.claude/` → "docs: ..." (usually documentation)

### 3. Generate Commit Messages

Template-based message generation:

```typescript
function generateCommitMessage(file: string, changes: string): string {
  const category = categorizeFile(file);
  const changeType = analyzeChanges(changes);
  const scope = extractScope(file);

  return `${category}${scope}: ${changeType}
  
${generateDescription(file, changes)}

🤖 Generated with Claude Code

Co-Authored-By: Claude (AI Assistant)`;
}
```

### 4. Interactive Confirmation

For each file:

- Show the file path
- Show a summary of changes
- Show the proposed commit message
- Ask for confirmation or allow editing

## Safety Features

- **Dry Run Mode**: Option to preview all commits without executing
- **Skip Files**: Option to skip specific files
- **Edit Messages**: Allow editing generated commit messages
- **Batch Confirmation**: Option to approve all or review each individually

## Example Usage

```bash
# Preview mode (shows what would be committed)
/project:commit-files-individually --dry-run

# Interactive mode (confirm each file)
/project:commit-files-individually --interactive

# Auto mode (commit all with generated messages)
/project:commit-files-individually --auto

# Skip certain patterns
/project:commit-files-individually --skip="*.test.ts,docs/*"
```

## Implementation Details

The command should be implemented as a comprehensive script that:

1. **Validates Git State**: Ensures we're on the right branch and have changes
2. **Analyzes Each File**: Uses git diff and file content analysis
3. **Generates Smart Messages**: Context-aware commit message generation
4. **Handles Edge Cases**: Binary files, renamed files, large changes
5. **Progress Reporting**: Shows which file is being processed (X of Y)

## File Categories and Message Templates

### Documentation Files (`*.md`)

```
docs: improve formatting and readability of [component] guide
docs: add comprehensive guide for [topic]
docs: update [component] documentation with latest changes
```

### Configuration Files

```
config: update [tool] configuration for [purpose]
config: add [setting] to improve [aspect]
```

### Test Files

```
test: fix [component] test failures and improve coverage
test: add missing tests for [functionality]
test: improve test reliability and reduce flakiness
```

### Source Code

```
feat: add [functionality] to [component]
fix: resolve [issue] in [component]
refactor: improve [aspect] of [component]
```

### Scripts

```
scripts: add [tool] for [purpose]
scripts: improve [script] functionality and error handling
```

## Advanced Features

### Change Analysis

- **Formatting Only**: Detect whitespace/formatting changes
- **Functionality Changes**: Detect logic modifications
- **New Features**: Detect new functions/components
- **Bug Fixes**: Detect error handling improvements

### Message Customization

- **Scope Detection**: Extract component/module names from file paths
- **Context Awareness**: Use surrounding files for context
- **Change Magnitude**: Adjust message detail based on change size

### Conflict Resolution

- **Large Files**: Handle files with extensive changes
- **Binary Files**: Appropriate messages for non-text files
- **Generated Files**: Special handling for auto-generated content

## Error Handling

- **Git Failures**: Graceful handling of git command failures
- **Permission Issues**: Clear error messages for access problems
- **Merge Conflicts**: Detection and appropriate messaging
- **Empty Changes**: Skip files with no meaningful changes

## Future Enhancements

- **AI Message Generation**: Use LLM to generate even smarter commit messages
- **Template Customization**: Allow project-specific message templates
- **Conventional Commits**: Enforce conventional commit standards
- **Changelog Integration**: Auto-update CHANGELOG.md with commits
- **PR Description**: Generate PR descriptions from individual commits

This command would significantly streamline the process of committing large changesets while maintaining clean, descriptive git history.
