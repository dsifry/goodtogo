---
model: claude-haiku-4-5-20251001
---

# Debug Onboarding Issues

Debug onboarding issues for a specific user by checking their current phase, recent activity, and providing reset options.

## Usage

```
/project:debug-onboarding <user-email>
```

## Steps

1. Run `pnpm onboarding:status --email=$ARGUMENTS --verbose` to check current status
2. Check recent failed jobs in the database for this user
3. Review their contact count and campaign status
4. If needed, suggest appropriate reset phase based on their situation
5. Provide specific commands to resolve their issue
6. Reference the [ONBOARDING_PHASE_RESET_ADMIN_GUIDE.md](../../docs/ONBOARDING_PHASE_RESET_ADMIN_GUIDE.md) for detailed procedures

Always use `--dry-run` first before making any changes to user accounts.
