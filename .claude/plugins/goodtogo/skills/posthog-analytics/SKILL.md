# posthog-analytics

Use when investigating user behavior, analytics, feature flag states, or debugging user issues by querying PostHog production data.

## When to Activate

Activate this skill when ANY of these conditions are true:

- User asks about analytics, metrics, or user behavior
- Need to check feature flag states for users
- Debugging why a user experienced a specific issue
- Investigating conversion funnels or user journeys
- Querying events for a specific user or cohort
- Checking dashboard or insight data
- Investigating LLM/AI generation costs or performance

## Announce at Start

"I'm using the posthog-analytics skill to securely query PostHog data."

## Security: Loading Credentials

**CRITICAL: Never echo, log, or display API keys in commands or output.**

```bash
# Secure credential loading - ALWAYS use this pattern
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a
```

**Never do this:**

```bash
# WRONG - exposes key in command history
curl -H "Authorization: Bearer phx_abc123..."

# WRONG - exposes key in output
echo "Key: $POSTHOG_READ_ONLY_KEY"
```

## Projects

| Project ID | Name              | Use Case                   |
| ---------- | ----------------- | -------------------------- |
| 104002     | Production        | Real user data & analytics |
| 118588     | Local development | Testing/dev events         |

**Default to 104002 for all production queries.**

---

## Quick Reference: Event Categories

### Onboarding & Trial Events

| Event                               | Description                    |
| ----------------------------------- | ------------------------------ |
| `onboarding_field_started`          | User started typing in a field |
| `onboarding_field_completed`        | User finished a field          |
| `onboarding_step_transition`        | User moved to next step        |
| `onboarding_completed`              | Full onboarding finished       |
| `onboarding_checkpoint_reached`     | Key milestone reached          |
| `onboarding_phase_completed`        | Phase 1/2/3 completed          |
| `onboarding_dropout_risk_detected`  | User at risk of abandoning     |
| `trial_started`                     | Trial period began             |
| `trial_expired`                     | Trial ended without conversion |
| `trial_converted_to_paid`           | User upgraded to paid          |
| `trial_activation_score_calculated` | Activation score computed      |
| `trial_churn_risk_detected`         | High churn risk identified     |

### Draft & Contact Events

| Event                        | Description                |
| ---------------------------- | -------------------------- |
| `drafts_created`             | Email drafts generated     |
| `drafts_creation_failed`     | Draft generation failed    |
| `contact_updated`            | Contact record modified    |
| `contact_deleted`            | Contact soft-deleted       |
| `contact_scoring_failed`     | Scoring pipeline error     |
| `linkedin_processing_failed` | LinkedIn data fetch failed |

### Campaign Events

| Event                  | Description          |
| ---------------------- | -------------------- |
| `campaign_created`     | New campaign created |
| `campaign_deactivated` | Campaign turned off  |

### Billing & Subscription

| Event                        | Description            |
| ---------------------------- | ---------------------- |
| `user_cancel_subscription`   | User cancelled         |
| `subscription_state_updated` | Subscription changed   |
| `trial_conversion_step`      | Conversion funnel step |

### System & Errors

| Event                          | Description                 |
| ------------------------------ | --------------------------- |
| `javascript_error_occurred`    | Client-side error           |
| `unhandled_promise_rejection`  | Promise error               |
| `react_query_error`            | Data fetching error         |
| `job_unblocked`                | Background job resumed      |
| `stale_blocked_jobs_recovered` | Old blocked jobs cleaned up |
| `circuit_open`                 | Circuit breaker opened      |
| `ai_fallback`                  | AI fallback triggered       |

### LLM/AI Events

| Event            | Description                           |
| ---------------- | ------------------------------------- |
| `$ai_generation` | PostHog standard LLM generation event |

**LLM Event Properties:**

- `$ai_trace_id` - Unique trace identifier
- `$ai_model` - Model used (gpt-5-nano, claude-3-7-sonnet)
- `$ai_provider` - Provider (openai, anthropic)
- `$ai_input_tokens` - Input token count
- `$ai_output_tokens` - Output token count
- `$ai_total_tokens` - Total token usage
- `$ai_latency` - Response time in seconds
- `$ai_service` - Service that made the call (e.g., "FocusedDraftGenerationService")
- `$ai_input` - Full prompt (system + user)
- `$ai_output` - Full response

**Active Models (last 7 days snapshot):**

- `gpt-4o-mini-2024-07-18` - ~22.9k calls (bulk operations)
- `gpt-5-nano` - ~25 calls, ~86k tokens
- `gpt-5-nano-2025-08-07` - ~13 calls
- `claude-3-7-sonnet-20250219` - ~1 call

---

## Dashboards (Production)

| ID     | Name                         | Use Case                         |
| ------ | ---------------------------- | -------------------------------- |
| 621660 | Conversion (Simplified)      | Conversion funnel overview       |
| 604003 | Feature Adoption Funnel      | Feature usage tracking           |
| 603999 | Onboarding Health            | Onboarding metrics & dropoff     |
| 616469 | Onboarding (Simplified)      | Quick onboarding overview        |
| 604000 | Trial & Conversion Analytics | Trial-to-paid funnel             |
| 621843 | Retention (Simplified)       | User retention metrics           |
| 616440 | Marketing (Simplified)       | Marketing analytics              |
| 374200 | AARRR – Pirate Metrics       | Acquisition/Activation/Retention |
| 388357 | trial-duration Usage         | Trial duration flag usage        |
| 313683 | onboarding-flow Usage        | Onboarding flow flag usage       |

### Quick Dashboard Access

```bash
# Open dashboard in browser (replace ID)
open "https://us.posthog.com/project/104002/dashboard/604000"
```

---

## Feature Flags (Live)

| Flag Key                 | Active | Purpose                             |
| ------------------------ | ------ | ----------------------------------- |
| `trial-duration`         | ✅     | Control trial length (returns days) |
| `payment-integration`    | ✅     | Enable/disable payment features     |
| `onboarding-flow`        | ✅     | Control onboarding flow             |
| `campaign-creation-tour` | ❌     | Show campaign creation tour         |

**Codebase also references:**

- `two-stage-drafts` - Enable two-stage draft generation
- `two-stage-shadow-mode` - Shadow mode for two-stage rollout

---

## Common Query Patterns

### Verify Authentication

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s "https://us.posthog.com/api/users/@me/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" | jq '{email: .email, org: .organization.name}'
```

### List Dashboards

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s "https://us.posthog.com/api/projects/104002/dashboards/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" | \
  jq -r '.results[] | "\(.id): \(.name)"'
```

### Check Feature Flags

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s "https://us.posthog.com/api/projects/104002/feature_flags/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" | \
  jq -r '.results[] | "\(.key): active=\(.active)"'
```

### Get Feature Flag State for User

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

USER_ID="user-distinct-id-here"
curl -s -X POST "https://us.posthog.com/api/projects/104002/feature_flags/local_evaluation/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"distinct_id\": \"${USER_ID}\"}" | jq '.'
```

---

## LLM Analytics Queries

### AI Generation Costs (Last 7 Days)

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT properties.$ai_model as model, count() as calls, sum(properties.$ai_total_tokens) as total_tokens, avg(properties.$ai_latency) as avg_latency_sec FROM events WHERE event = '"'"'$ai_generation'"'"' AND timestamp > now() - INTERVAL 7 DAY GROUP BY model ORDER BY total_tokens DESC"
    }
  }' | jq '.results'
```

### AI Calls by Service

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT properties.$ai_service as service, count() as calls, sum(properties.$ai_total_tokens) as tokens FROM events WHERE event = '"'"'$ai_generation'"'"' AND timestamp > now() - INTERVAL 7 DAY GROUP BY service ORDER BY tokens DESC"
    }
  }' | jq '.results'
```

### Slow AI Calls (>5s)

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT timestamp, properties.$ai_model as model, properties.$ai_service as service, properties.$ai_latency as latency_sec FROM events WHERE event = '"'"'$ai_generation'"'"' AND properties.$ai_latency > 5 AND timestamp > now() - INTERVAL 24 HOUR ORDER BY latency_sec DESC LIMIT 20"
    }
  }' | jq '.results'
```

---

## User Investigation Queries

### Recent Events for User (by email)

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

EMAIL="user@example.com"
curl -s "https://us.posthog.com/api/projects/104002/persons/?email=${EMAIL}" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" | \
  jq '.results[0] | {distinct_ids, properties}'
```

### User Journey (Last 50 Events)

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

USER_ID="user-distinct-id-here"
curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": {
      \"kind\": \"HogQLQuery\",
      \"query\": \"SELECT timestamp, event, properties FROM events WHERE distinct_id = '${USER_ID}' ORDER BY timestamp DESC LIMIT 50\"
    }
  }" | jq '.results'
```

### Trial Users Overview

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT toDate(timestamp) as day, count() as trials_started FROM events WHERE event = '"'"'trial_started'"'"' AND timestamp > now() - INTERVAL 30 DAY GROUP BY day ORDER BY day DESC"
    }
  }' | jq '.results'
```

---

## Onboarding Analytics

### Onboarding Completion Rate

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT count(DISTINCT if(event = '"'"'onboarding_field_started'"'"', distinct_id, NULL)) as started, count(DISTINCT if(event = '"'"'onboarding_completed'"'"', distinct_id, NULL)) as completed FROM events WHERE timestamp > now() - INTERVAL 30 DAY"
    }
  }' | jq '.results'
```

### Dropout Risk Detection

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT distinct_id, timestamp, properties FROM events WHERE event = '"'"'onboarding_dropout_risk_detected'"'"' AND timestamp > now() - INTERVAL 7 DAY ORDER BY timestamp DESC LIMIT 20"
    }
  }' | jq '.results'
```

---

## Daily Metrics Queries

### Daily Active Users (Last 30 Days)

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT toDate(timestamp) as day, count(DISTINCT distinct_id) as users FROM events WHERE timestamp > now() - INTERVAL 30 DAY GROUP BY day ORDER BY day DESC"
    }
  }' | jq -r '.results[] | "\(.[0]): \(.[1]) users"'
```

### Event Counts by Type (Last 7 Days)

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT event, count() as count FROM events WHERE timestamp > now() - INTERVAL 7 DAY GROUP BY event ORDER BY count DESC LIMIT 30"
    }
  }' | jq -r '.results[] | "\(.[1]): \(.[0])"'
```

### Error Rate (Last 24 Hours)

```bash
set -a && source /Users/dsifry/Developer/goodtogo/.env && set +a

curl -s -X POST "https://us.posthog.com/api/projects/104002/query/" \
  -H "Authorization: Bearer $POSTHOG_READ_ONLY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "kind": "HogQLQuery",
      "query": "SELECT event, count() as count FROM events WHERE event IN ('"'"'javascript_error_occurred'"'"', '"'"'unhandled_promise_rejection'"'"', '"'"'react_query_error'"'"', '"'"'drafts_creation_failed'"'"', '"'"'contact_scoring_failed'"'"') AND timestamp > now() - INTERVAL 24 HOUR GROUP BY event ORDER BY count DESC"
    }
  }' | jq '.results'
```

---

## API Capabilities

| Endpoint                            | Description    | Example Use           |
| ----------------------------------- | -------------- | --------------------- |
| `/api/projects/`                    | List projects  | Verify access         |
| `/api/projects/{id}/dashboards/`    | Dashboards     | View saved dashboards |
| `/api/projects/{id}/insights/`      | Saved insights | Retrieve analyses     |
| `/api/projects/{id}/feature_flags/` | Feature flags  | Check flag states     |
| `/api/projects/{id}/events/`        | Raw events     | Debug user actions    |
| `/api/projects/{id}/persons/`       | User profiles  | Look up users         |
| `/api/projects/{id}/cohorts/`       | User cohorts   | Segment analysis      |
| `/api/projects/{id}/query/`         | HogQL queries  | Custom analytics      |
| `/api/users/@me/`                   | Current user   | Verify auth           |

---

## HogQL Quick Reference

| Table     | Contents            |
| --------- | ------------------- |
| `events`  | All captured events |
| `persons` | User profiles       |
| `groups`  | Group analytics     |

**Common `events` fields:**

- `event` - Event name
- `distinct_id` - User identifier
- `timestamp` - When it occurred
- `properties` - JSON object of event properties
- `person_id` - Link to persons table

**Accessing properties:**

```sql
-- Dot notation for simple access
properties.$ai_model

-- Bracket notation for special characters
properties['$ai_model']
```

---

## Troubleshooting

### Shell Variable Loading Issues

If `set -a && source .env` doesn't work (variable appears empty in curl), extract the key directly:

```bash
# Extract key directly from .env file
KEY=$(grep "^POSTHOG_READ_ONLY_KEY=" /Users/dsifry/Developer/goodtogo/.env | cut -d'=' -f2)

# Use in curl
curl -s "https://us.posthog.com/api/projects/104002/dashboards/" \
  -H "Authorization: Bearer ${KEY}" | jq '.'
```

### Authentication Not Working

If you get `"Authentication credentials were not provided"`:

1. Check the key exists in .env: `grep POSTHOG_READ_ONLY_KEY /Users/dsifry/Developer/goodtogo/.env`
2. Verify key prefix is `phx_` (personal API key)
3. If key is expired/invalid, generate a new Personal API Key:
   - Go to [PostHog User API Keys](https://us.posthog.com/settings/user-api-keys)
   - Create new key with read permissions for project 104002
   - Update `.env` with `POSTHOG_READ_ONLY_KEY=phx_...`

### Wrong Project

- **104002** = Production (real users) - USE THIS
- **118588** = Local development (test data only)

### Output Formatting

```bash
# Use jq for JSON parsing
... | jq '.results'

# Use table format for lists
... | jq -r '.results[] | "\(.id)\t\(.name)"' | column -t

# Limit output for large datasets
... | jq '.results[:10]'
```

---

## Verification Checklist

Before completing any analytics query:

- [ ] Credentials loaded securely (no keys in commands)
- [ ] Using correct project ID (104002 for production)
- [ ] Output formatted and readable
- [ ] Sensitive user data handled appropriately
