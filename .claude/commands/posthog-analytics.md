---
description: Query PostHog production data for analytics, feature flags, and user debugging
---

# PostHog Analytics

Securely query PostHog for user behavior, analytics, LLM costs, and feature flag states.

## Usage

```bash
/project:posthog-analytics
```

## Quick Reference

| Query Type         | Example Use Case                          |
| ------------------ | ----------------------------------------- |
| LLM Analytics      | AI costs, token usage, slow calls         |
| User Investigation | Debug user issues, view journey           |
| Onboarding Metrics | Completion rates, dropout risk            |
| Trial Analytics    | Conversion, churn risk, activation scores |
| Error Monitoring   | JS errors, failed operations              |
| Feature Flags      | Check flag states for users               |

## Projects

- **104002** - Production (use this for all queries)
- **118588** - Local development only

## Steps

1. **Activate the posthog-analytics skill**:
   Load and follow `.claude/plugins/goodtomerge/skills/posthog-analytics/SKILL.md`

2. **Query PostHog** following the skill's secure patterns for credential handling

## Common Shortcuts

```bash
# LLM costs by model (last 7 days)
/project:posthog-analytics → "AI generation costs by model"

# User journey debugging
/project:posthog-analytics → "Events for user@example.com"

# Onboarding funnel
/project:posthog-analytics → "Onboarding completion rate"

# Error monitoring
/project:posthog-analytics → "Errors in last 24 hours"
```

## Troubleshooting Auth

If API calls fail, generate a new Personal API Key:

1. Go to [PostHog User API Keys](https://us.posthog.com/settings/user-api-keys)
2. Create key with read permissions
3. Update `.env` with `POSTHOG_READ_ONLY_KEY=phx_...`
