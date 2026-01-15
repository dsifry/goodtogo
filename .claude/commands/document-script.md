# Document Script Command

This command provides a template for documenting utility scripts in the `scripts/` directory.

## Usage

```
/project:document-script <script-name>
```

## Documentation Template

When documenting a script, create a file in `docs/` named `<SCRIPT_NAME_UPPERCASE>_SCRIPT.md` with the following structure:

````markdown
# [Script Name] Script

## Purpose

[Brief description of what this script does and why it exists]

## Usage

```bash
npx tsx scripts/[script-name].ts [options]
```
````

## Options

| Option        | Alias | Type    | Description                    | Default    |
| ------------- | ----- | ------- | ------------------------------ | ---------- |
| `--userEmail` | `-u`  | string  | User email to process          | Required\* |
| `--all-users` | `-a`  | boolean | Process all active users       | false      |
| `--verbose`   | `-v`  | boolean | Enable verbose logging         | false      |
| `--dry-run`   |       | boolean | Preview changes without saving | false      |

\*Required unless `--all-users` is specified

## Examples

### Process Single User

```bash
npx tsx scripts/[script-name].ts --userEmail user@example.com
```

### Process All Users with Verbose Output

```bash
npx tsx scripts/[script-name].ts --all-users --verbose
```

### Dry Run Mode

```bash
npx tsx scripts/[script-name].ts --userEmail user@example.com --dry-run
```

## Output

[Describe what output the script produces - console logs, files, database updates, etc.]

## Error Handling

[Describe how the script handles errors and what error messages mean]

## Dependencies

- Requires database connection
- Requires Redis connection (if applicable)
- Requires API credentials: [list any required env vars]

## Related Scripts

- [List any related scripts that do similar things or work together]

## Implementation Notes

[Any important implementation details, known limitations, or future improvements]

```

## Example Documentation

See existing script documentation:
- `docs/CHECK_LINKEDIN_DATA_SCRIPT.md`
- `docs/CHECK_LINKEDIN_URLS_SCRIPT.md`
- `docs/CHECK_CONTACT_SUMMARY_SCRIPT.md`

## Best Practices

1. **Be Specific**: Include exact command examples that can be copy-pasted
2. **Document All Options**: Even if they seem obvious
3. **Show Real Examples**: Use realistic email addresses and data
4. **Explain Output**: Help users understand what they're seeing
5. **List Dependencies**: Make it clear what's needed to run the script
6. **Cross-Reference**: Link to related scripts and documentation
```
