# Script Development Guide

This guide covers best practices for developing and managing utility scripts in the `scripts/` directory.

## Script Management Guidelines

When working with utility scripts:

1. **Assessment First**: Always check if a script already exists before creating a new one
2. **Generalization Pattern**: Replace hardcoded values with CLI arguments using yargs
3. **Documentation**: Create documentation in `docs/` for each generalized script
4. **Cleanup**: Remove redundant scripts that duplicate functionality
5. **Managed Files**: Update @.claude/MANAGED_FILES.md for scripts to keep

## Common Script Patterns

### CLI Arguments with Yargs

```typescript
// Use yargs for CLI arguments
import yargs from "yargs";
import { hideBin } from "yargs/helpers";

const argv = await yargs(hideBin(process.argv))
  .option("userEmail", {
    alias: "u",
    type: "string",
    description: "User email to process",
  })
  .option("all-users", {
    alias: "a",
    type: "boolean",
    description: "Process all users",
  })
  .parse();
```

## Script Type Safety

For TypeScript patterns in scripts, see @.claude/guides/typescript-patterns.md#script-type-safety

Key principles:

- Never use `any` types
- Define interfaces for JSON data
- Use type guards for dynamic data
- Extract nullable values before comparisons

## Script Execution

- **Environment Setup**: Always run `source .env` before executing scripts that require API credentials
- **TypeScript Scripts**: Use `npx tsx` to run TypeScript scripts directly
- **Timeout Considerations**: Use appropriate timeouts for long-running scripts (see timeout guidelines below)

## Script Documentation Template

When documenting scripts, use @.claude/commands/document-script.md template

## Recommended Script Timeouts

| Script Type           | Timeout (ms) | Duration   | Usage              |
| --------------------- | ------------ | ---------- | ------------------ |
| Data processing       | 300000       | 5 minutes  | Bulk operations    |
| API collection        | 180000       | 3 minutes  | External API calls |
| Database migrations   | 180000       | 3 minutes  | Schema changes     |
| Pipeline testing      | 180000       | 3 minutes  | Full AI pipeline   |
| Large file operations | 600000       | 10 minutes | Maximum allowed    |

## Operational Scripts

### Onboarding Outreach & Re-engagement

The most comprehensive operational script for user re-engagement:

- **Script**: `npx tsx scripts/onboarding-outreach.ts`
- **Purpose**: Re-engage incomplete onboarding, never-started, and unconverted users
- **Key Features**:
  - AI-enhanced email personalization with multiple providers (Anthropic, OpenAI)
  - 6 sales methodologies (Carnegie, Hormozi, Ross, Bertuzzi, Braun, combined)
  - Gmail draft creation with CSV tracking for analytics
  - Incremental campaign support with duplicate prevention

**Core Options**:

```bash
--userEmail <email>         # Gmail account for drafts (required)
--output <path>            # CSV output path (required, use /data/)
--allEligible              # Process all user segments
--useAI                    # Enable AI enhancement
--salesMethodology <name>  # Sales approach
--excludeFromCsv <path>    # Exclude previous contacts
--createdAfter <date>      # Only new users
--dry-run                  # Preview mode
```

**Production Example**:

```bash
npx tsx scripts/onboarding-outreach.ts \
  --allEligible \
  --userEmail ceo@company.com \
  --output ./data/outreach-$(date +%Y-%m-%d).csv \
  --useAI \
  --salesMethodology carnegie \
  --excludeFromCsv ./data/previous-week.csv
```

**See**: @docs/ONBOARDING_OUTREACH_GUIDE.md for comprehensive documentation

### Score and Draft Pipeline Testing

- `npx tsx scripts/test-score-and-draft-pipeline.ts --userEmail <email>`
- Options:
  - `--verbose` - Full output
  - `--debug` - HTML/JSON output
  - `--raw` - Complete data dump
  - `--no-cache` - Fresh LinkedIn data
  - `--raw-prompts` - Show AI prompts
- See @docs/TEST_SCORE_AND_DRAFT_PIPELINE.md for details

## Best Practices

1. **Error Handling**: Always include try-catch blocks with meaningful error messages
2. **Progress Feedback**: Use console.log to show progress for long-running operations
3. **Dry Run Mode**: Consider adding `--dry-run` option for dangerous operations
4. **Data Validation**: Validate input data before processing
5. **Idempotency**: Design scripts to be safely re-runnable

## Script Organization

- Place scripts in `scripts/` directory
- Use descriptive names (e.g., `migrate-user-data.ts` not `script1.ts`)
- Group related scripts in subdirectories if needed
- Keep test data in `/data/` directory (ensure in .gitignore)

## See Also

- @docs/TYPESCRIPT_SCRIPTS_USAGE.md for TypeScript script execution
- @.claude/guides/typescript-patterns.md for type safety patterns
- @.claude/commands/document-script.md for documentation template
