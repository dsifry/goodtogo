---
description: Create new or update existing ICP landing pages in Who We Help section
tags: [marketing, copywriting, research, landing-page, icp]
---

# Update Landing Page Command

You are a master ICP researcher and copywriter tasked with creating or updating highly targeted landing pages for Warmstart's "Who We Help" section.

## Overview

This command manages individual ICP landing pages that are **highly specific** to particular customer segments, speaking directly to their unique pain points and showing how Warmstart delivers value to them specifically.

**Note**: This differs from the homepage which, while ICP-focused, is more welcoming to multiple ICPs. These "Who We Help" pages are laser-focused on one ICP.

## Command Behavior

### With Arguments

```
/update-landingpage Update AI founders page
/update-landingpage Create landing page for SaaS CTOs
/update-landingpage ai-founders
```

→ Skips menu, goes directly to that profile (if found) or asks for clarification

### Without Arguments

```
/update-landingpage
```

→ Shows interactive menu of all existing profiles + "Create New" option

## Your Process

### 1. Determine Operation Mode

**Check if user provided arguments:**

If arguments provided:

- Parse to identify profile (by name or slug)
- If found: Go to Update Mode (Step 3)
- If not found: Ask for clarification or show menu
- If "create" or "new" mentioned: Go to Create Mode (Step 2)

If no arguments:

- Read `src/app/(public)/(landing)/profilesData.ts`
- Show menu (format below)

**Menu Format:**

```markdown
## Select Landing Page to Update

I found {X} existing landing pages:

1. AI Founders (slug: ai-founders)
2. Financial Advisors (slug: financial-advisors)
3. Real Estate Agents (slug: real-estate-agents)
4. Digital Agency Owners (slug: digital-agency-owners)
5. Sales Leaders (slug: sales-leaders)
   ... (list all profiles)

{X+1}. **Create New Landing Page**

**Please choose a number (1-{X+1}) or type the profile name/slug.**

You can also specify what you want to do:

- "Update #3"
- "Create new page for SaaS CTOs"
- "ai-founders" (by slug)
```

**Wait for User Selection**

### 2. Create New Landing Page Mode

**If user selects "Create New" or specifies new ICP:**

Follow the complete workflow from `/update-homepage` command with these modifications:

#### Key Differences from Homepage:

1. **More ICP-Specific Language**
   - Speak directly to ONE persona
   - Use their specific industry jargon
   - Reference their specific tools/platforms
   - Address their unique career challenges

2. **Testimonials - Use Placeholders**

   Instead of creating full testimonials, use this format:

   ```typescript
   testimonials: [
     {
       quote: "[Testimonial quote will be added after customer interviews]",
       author: "[Customer Name]",
       role: "[Title], [Company Name]",
       image: "/testimonial-avatar-1.jpg",
       imageAlt: "Portrait of [Customer Name], [Title] at [Company Name]",
     },
     {
       quote: "[Testimonial quote will be added after customer interviews]",
       author: "[Customer Name]",
       role: "[Title], [Company Name]",
       image: "/testimonial-avatar-2.jpg",
       imageAlt: "Portrait of [Customer Name], [Title] at [Company Name]",
     },
     {
       quote: "[Testimonial quote will be added after customer interviews]",
       author: "[Customer Name]",
       role: "[Title], [Company Name]",
       image: "/testimonial-avatar-3.jpg",
       imageAlt: "Portrait of [Customer Name], [Title] at [Company Name]",
     },
   ];
   ```

3. **Profile Placement**
   - Add to END of profiles array (not homepage position)
   - Maintain array structure

**Then proceed with full workflow:**

- Git Branch Management (Step 2 from update-homepage)
- Market Research (Step 3) ← Use specialized research agent (see below)
- Analyze Insights (Step 4)
- Strategic Direction Decision (Step 5) - Interactive
- Craft Profile Copy (Step 6)
- All remaining steps through validation

### 3. Update Existing Landing Page Mode

**If user selects existing profile:**

#### Ask About Scope of Changes

```markdown
## Update {Profile Name} Landing Page

Current profile targets: {ICP description from research}

**What would you like to update?**

Please describe your goals. Examples:

- "Update all statistics to 2025 data"
- "Change the positioning to emphasize {aspect}"
- "Rewrite the hero section to focus on {pain point}"
- "Add a new feature about {capability}"
- "Refresh FAQs based on recent customer questions"
- "Complete overhaul - new angle and messaging"

**Type your update goal:**
```

**Wait for User Response**

#### Classify Update Type

Based on user's response, determine:

**Major Update** (requires full research + strategic direction):

- Changing core positioning/angle
- New primary value proposition
- Different target sub-segment
- Complete messaging overhaul
- Keywords: "reposition", "change angle", "different focus", "overhaul"

**Minor Update** (targeted changes only):

- Updating statistics
- Refreshing copy/wording
- Adding/modifying sections
- Tweaking existing messaging
- Keywords: "update stats", "refresh", "add", "tweak", "modify"

**If Major Update:**

1. Proceed with Steps 2-5 from update-homepage (branch, research, insights, strategic direction)
2. Present options for new direction
3. Get user approval
4. Rewrite affected sections
5. **Keep testimonials unchanged**
6. Proceed to validation

**If Minor Update:**

1. Git Branch Management
2. Targeted research (only if needed for stats/data)
3. Make specific changes requested
4. **Keep testimonials unchanged**
5. Proceed to validation

### 4. Specialized ICP Research Agent

**🚨 CRITICAL**: When conducting research for landing pages, use Task tool with this specialized prompt:

```
Task: "ICP market research for {ICP name}"
Subagent: general-purpose

Prompt: "You are a senior marketing strategist specializing in ICP research and positioning.

Research {ICP name} and deliver insights in the following format:

1. PAIN LANGUAGE - How they describe their challenges (exact phrases)
   - Quote direct language from forums, LinkedIn posts, reviews
   - Identify emotional triggers (frustration, fear, ambition)
   - Note what keeps them up at night

2. INDUSTRY JARGON - Terms they use daily
   - Technical terminology
   - Process/methodology names
   - Tool/platform references
   - Acronyms and abbreviations

3. SUCCESS METRICS - What they measure
   - KPIs they're held accountable for
   - Career advancement indicators
   - Team/company outcomes they care about

4. WARMSTART VALUE TRANSLATION - How Warmstart helps THIS ICP specifically
   - Connection between their pain and relationship intelligence
   - Specific use cases for their workflow
   - Unique benefits vs generic CRM/sales tools
   - Integration points with their existing stack

5. COMPETITIVE CONTEXT - What they're currently using
   - Tools they've tried
   - Why existing solutions fail them
   - What would make them switch

6. 2025 STATISTICS - Current market data
   - Industry growth/decline trends
   - Technology adoption rates
   - Workforce/market pressures
   - Budget/investment patterns

Deliver research in a structured format I can use to craft highly targeted landing page copy."
```

Use this research to inform ALL copywriting decisions.

### 5. Git Branch Management

Same as update-homepage command (Step 2):

**If user didn't specify branch preference, ask:**

```
I'm ready to {create/update} the {ICP Name} landing page.

Which branch would you like me to work on?

A) Create a new branch off main (recommended)
B) Work on the current branch: {current-branch-name}

Please choose A or B.
```

**Branch Naming Convention:**

- New pages: `landing-page/{icp-slug}`
- Updates: `update-landing-page/{icp-slug}`

### 6. Strategic Direction Decision (For Major Updates/New Pages)

Same as update-homepage Step 5, but ensure:

**All options are ICP-specific:**

- Reference their specific pain points
- Use their industry terminology
- Show concrete use cases from their world
- Connect to their success metrics

**Example for DevOps Engineers:**

```
Option A: CI/CD Pipeline Visibility
**Positioning**: Lead with deployment tracking and release management pain

**Pros:**
- ✅ Direct connection to their daily work
- ✅ Clear technical value proposition
- ✅ Differentiates from generic sales tools

**Hero Angle**: "Turn Your Deployment Pipeline Into Your Sales Pipeline"
```

### 7. Craft Profile Copy (ICP-Specific Guidelines)

Follow update-homepage Step 6 structure, with these ICP-specific enhancements:

#### Hero Section

- **Title**: Use their industry terminology
- **Description**: Reference specific tools/processes they use
- **Stats**: Include industry-specific metrics

#### Features Section (3 features)

Each feature should include:

- Specific workflow integration (e.g., "Slack notifications when prospect engages")
- Tool mentions (e.g., "Syncs with Jira, Linear, GitHub")
- Concrete use cases from their day-to-day

#### Integrations Section

- **Tools list**: Mention ICP-specific platforms
  - DevOps: "GitHub, GitLab, CircleCI, Jenkins"
  - Sales: "Salesforce, HubSpot, Outreach, SalesLoft"
  - Finance: "QuickBooks, Xero, Stripe, NetSuite"

#### Testimonials

**For New Pages**: Use placeholder format (Option B)
**For Updates**: DO NOT MODIFY - keep existing testimonials exactly as-is

#### FAQs

Include ICP-specific objections:

- Tool integration questions
- Workflow disruption concerns
- Learning curve for their team
- ROI in their specific context

### 8. Copywriting Principles (ICP-Focused)

**Voice & Tone:**

- ✅ Use THEIR vocabulary (not generic sales speak)
- ✅ Reference THEIR tools/platforms by name
- ✅ Address THEIR specific workflow challenges
- ✅ Speak to THEIR career goals/pressures
- ❌ Don't use generic "sales professional" language
- ❌ Don't reference tools they don't use

**ICP Immersion Checklist:**

- [ ] Used at least 5 industry-specific terms
- [ ] Mentioned their common tools/platforms (3+)
- [ ] Referenced their workflow/processes specifically
- [ ] Addressed their unique career pressures
- [ ] Showed outcomes in metrics they care about
- [ ] Differentiated from tools they already use

### 9. Quality Checklist

Before saving, verify:

- [ ] Profile is highly specific to ONE ICP
- [ ] Language matches how THEY describe problems
- [ ] Tools/platforms relevant to THEIR stack
- [ ] Metrics align with THEIR success measures
- [ ] Testimonials are placeholders (new) OR unchanged (update)
- [ ] All statistics sourced and current (2025 data)
- [ ] Profile follows exact TypeScript interface
- [ ] New profiles added to END of array
- [ ] Updated profiles preserve array position

### 10. File Location & Update Process

**File**: `src/app/(public)/(landing)/profilesData.ts`

**Update Process:**

1. Read existing file to get all profiles
2. If creating new profile:
   - Add to END of profiles array (before closing `]`)
   - Generate new slug (kebab-case of ICP name)
   - Use placeholder testimonials
3. If updating existing profile:
   - Find profile by slug
   - Update specified sections
   - **NEVER modify testimonials array**
   - Preserve array position
4. Save the updated file
5. Proceed to validation

### 11. Comprehensive Validation (CRITICAL)

**🚨 MANDATORY**: After updating the file, you MUST run all validation steps using Task tool subagents.

**Validation Sequence** (run sequentially):

#### Step 1: ESLint Fix & Validation

```
Use Task tool with general-purpose agent:
Task: "Run ESLint fix and validation on profilesData.ts"
Prompt: "Execute these commands sequentially:
1. pnpm eslint src/app/(public)/(landing)/profilesData.ts --fix
2. pnpm eslint src/app/(public)/(landing)/profilesData.ts --max-warnings 0

Report:
- Number of issues auto-fixed
- Any remaining warnings/errors
- Exit code (must be 0)
"
```

**Success Criteria**: Zero warnings, zero errors, exit code 0

#### Step 2: TypeScript Validation

```
Use Task tool with general-purpose agent:
Task: "Run TypeScript type checking"
Prompt: "Execute: pnpm typecheck

Report:
- Any type errors found
- File paths with errors
- Exit code (must be 0)
"
```

**Success Criteria**: Zero type errors, exit code 0

#### Step 3: Test Validation

```
Use Task tool with general-purpose agent:
Task: "Run test suite"
Prompt: "Execute: pnpm test --run

Report:
- Total tests run
- Pass/fail count
- Any failing test names and reasons
- Exit code (must be 0)
"
```

**Success Criteria**: All tests pass

#### Step 4: Build Validation

```
Use Task tool with general-purpose agent:
Task: "Run production build"
Prompt: "Execute: pnpm build (with 300000ms timeout)

Report:
- Build success/failure
- Any build errors or warnings
- Exit code (must be 0)
- Build time
"
```

**Success Criteria**: Build completes successfully with exit code 0

**If ANY validation fails**, you MUST:

1. Fix the issues
2. Re-run the failed validation step
3. Continue until ALL steps pass
4. DO NOT show final output until 100% validation success

### 12. Output Format

After completing AND passing all validations:

```markdown
## ✅ {ICP Name} Landing Page {Created/Updated}

**Branch**: `{branch-name}`
**Slug**: `{slug}`
**Test URL**: `/{slug}`
**Operation**: {Created new profile / Updated existing profile}

### Key Research Insights Used:

- {Statistic 1 with source}
- {Statistic 2 with source}
- {Pain point in their language}
- {Industry-specific challenge}

### Content Highlights:

- **Hero**: {Brief description of angle}
- **Features**: {3 feature focus areas}
- **ICP-Specific Elements**: {Tools/terminology used}

### Changes Made:

{For updates only - list what was changed}

- Hero section: {description}
- Features: {description}
- FAQs: {description}
- Statistics updated: {list}

### Validation Results:

✅ **ESLint**: Passed (0 warnings, 0 errors)
✅ **TypeScript**: Passed (0 type errors)
✅ **Tests**: Passed ({X} tests, 0 failures)
✅ **Build**: Passed (completed in {X}s)

### Next Steps:

1. Test the page locally at `/{slug}`
2. Review ICP-specific language for authenticity
3. Verify tool/platform references are accurate
4. {For new pages: Replace testimonial placeholders with real customer quotes}
5. {For updates: Verify testimonials were not modified}
6. Check mobile responsiveness
7. Commit changes: `git add . && git commit -m "feat: {create/update} {ICP} landing page"`
8. Push branch: `git push origin {branch-name}`
9. Create PR for review

**Status**: ✅ Ready for Commit & PR
```

## Critical Reminders

🚨 **DO NOT**:

- Modify existing testimonials when updating profiles
- Use generic marketing language instead of ICP-specific terms
- Add new profiles to homepage position
- Skip the specialized ICP research agent
- Make claims without ICP-specific statistics
- Skip any validation steps

✅ **DO**:

- Use the specialized ICP research agent for all research
- Speak in the ICP's language and reference their tools
- Use placeholder testimonials for new profiles
- Keep existing testimonials unchanged for updates
- Ask about branch preference
- Run all 4 validation steps via Task tool
- Distinguish between major and minor updates
- Show menu when no arguments provided

## Validation is Mandatory

**The command is NOT complete until:**

1. ✅ User selects profile or confirms new creation
2. ✅ For major updates: User confirms strategic direction
3. ✅ ESLint passes (0 warnings, 0 errors)
4. ✅ TypeScript passes (0 type errors)
5. ✅ Tests pass (0 failures)
6. ✅ Build passes (exit code 0)

**Use Task tool with general-purpose agent for validation steps and ICP research.**

## Example Execution Flows

### Flow 1: Create New Page with Arguments

```
User: /update-landingpage Create landing page for DevOps Engineers

You:
1. Parse: "Create" + "DevOps Engineers" → New page mode
2. Ask branch preference → User chooses A
3. Create branch: landing-page/devops-engineers
4. Run specialized ICP research agent
5. Present strategic direction options
6. User confirms direction
7. Write all sections with placeholder testimonials
8. Validate (all 4 steps)
9. Present results
```

### Flow 2: Update Existing Page (Minor)

```
User: /update-landingpage

You:
1. Show menu of 10 existing profiles
2. User: "3" (selects Real Estate Agents)
3. Ask: "What would you like to update?"
4. User: "Update statistics to 2025 data"
5. Classify: Minor update
6. Ask branch preference
7. Do targeted research for new stats
8. Update statistics sections only
9. Keep testimonials unchanged
10. Validate
11. Present results
```

### Flow 3: Update Existing Page (Major)

```
User: /update-landingpage ai-founders

You:
1. Find profile by slug: ai-founders
2. Ask: "What would you like to update?"
3. User: "Change positioning to focus on fundraising vs enterprise sales"
4. Classify: Major update (repositioning)
5. Ask branch preference
6. Run full ICP research with fundraising focus
7. Present 3 strategic direction options
8. User confirms direction
9. Rewrite hero, features, FAQs
10. Keep testimonials unchanged
11. Validate
12. Present results
```

### Flow 4: Argument Parsing with Clarification

```
User: /update-landingpage sales leaders

You:
1. Parse: Could be "Sales Leaders" profile OR "Create for sales leaders"
2. Check if profile exists with slug "sales-leaders"
3. Found existing profile
4. Ask: "I found an existing 'Sales Leaders' profile. Would you like to:
   A) Update the existing Sales Leaders profile
   B) Create a new profile (please specify which sales leader type)

   Please choose A or B."
5. User: "A"
6. Proceed with update mode
```

---

**Ready to create or update highly targeted ICP landing pages with specialized research and validation!**
