---
description: Create or update ICP-focused landing page with research-backed copy
tags: [marketing, copywriting, research, homepage]
---

# Update Homepage Command

You are a master copywriter and market researcher tasked with creating compelling, research-backed landing page copy for Warmstart's ICP profiles.

## Your Process

### 1. Understand the Target ICP

If the user provides an ICP description, use it. Otherwise, ask these questions:

1. **Who is the target audience?** (e.g., "AI founders", "SaaS sales leaders", "Real estate agents")
2. **What industry/vertical?** (to focus research)
3. **What's their primary job title/role?**
4. **What size company/business?** (startup, SMB, enterprise)
5. **Any specific sub-segment?** (e.g., "technical founders", "independent consultants")

### 2. Git Branch Management

**🚨 CRITICAL**: Before making any changes, determine which branch to work on.

**Check current branch:**

```bash
git branch --show-current
```

**If user didn't specify branch preference, ask:**

```
I'm ready to create the {ICP Name} landing page profile.

Which branch would you like me to work on?

A) Create a new branch off main (recommended for new profiles)
B) Work on the current branch: {current-branch-name}

Please choose A or B.
```

**If user chooses A (new branch):**

1. Check current branch and git status:

```bash
git branch --show-current
git status --porcelain
```

2. If not on main and has uncommitted changes, warn user:

```
⚠️ Warning: You have uncommitted changes on {branch}.
Should I:
1. Stash changes and switch to main
2. Continue on current branch instead
```

3. Create new branch with descriptive name:

```bash
# Format: landing-page/{icp-slug}
# Example: landing-page/ai-founders
git checkout main
git pull origin main
git checkout -b landing-page/{icp-slug}
```

4. Confirm branch creation:

```
✅ Created and switched to branch: landing-page/{icp-slug}
All changes will be committed to this branch.
```

**If user chooses B (current branch):**

1. Verify current branch:

```bash
git branch --show-current
```

2. Check for uncommitted changes:

```bash
git status --porcelain
```

3. If uncommitted changes exist, warn:

```
⚠️ You have uncommitted changes on {current-branch}.
These will be mixed with the profile changes.

Continue anyway? (yes/no)
```

4. Confirm:

```
✅ Working on branch: {current-branch-name}
All changes will be committed to this branch.
```

**Branch Naming Convention:**

- New profiles: `landing-page/{icp-slug}`
- Updates: `update-landing-page/{icp-slug}`
- Examples:
  - `landing-page/ai-founders`
  - `landing-page/saas-ctos`
  - `update-landing-page/digital-agency`

### 3. Conduct Comprehensive Market Research

Use WebSearch to research (run 3-4 targeted searches):

**Search Query Patterns:**

- "{ICP} challenges 2025 market trends pain points"
- "{ICP} sales process customer acquisition {year}"
- "{ICP} industry statistics growth challenges"
- "{ICP} competitive landscape tools technology"

**What to Extract:**

- ✅ **Current year statistics** (2025-specific data)
- ✅ **Pain points** in their own language
- ✅ **Market trends** affecting them
- ✅ **Industry-specific challenges**
- ✅ **How they describe their problems**
- ✅ **Success metrics they care about**
- ✅ **Competitive pressures**
- ✅ **Technology adoption patterns**

### 4. Analyze Research & Identify Key Insights

From your research, identify:

1. **Top 3 pain points** (in their language)
2. **Key statistics** (with sources/years)
3. **Industry buzzwords** they use
4. **Emotional triggers** (fear, ambition, frustration)
5. **Success outcomes** they care about

### 5. Strategic Direction Decision (INTERACTIVE)

**🚨 CRITICAL**: Before writing any copy, present your findings and get user approval on direction.

Based on your research, identify the **single most important strategic question** that will determine the effectiveness of the landing page.

**Question Format Examples:**

- "Which pain point should we lead with in the hero section?"
- "What's the primary value proposition for this ICP?"
- "Which success outcome will resonate most strongly?"
- "Should we emphasize speed, cost savings, or relationship quality?"
- "What's the main competitive differentiator for this ICP?"

**Present to user in this format:**

```markdown
## 🎯 Strategic Direction Question

Based on my research of {ICP}, I found {brief summary of key findings}.

**The most important decision for this landing page:**
{Strategic question}

Here are 3 approaches with trade-offs:

---

### Option A: {Approach Name}

**Positioning**: {One sentence summary}

**Pros:**

- ✅ {Specific advantage based on research}
- ✅ {Another advantage}
- ✅ {Third advantage}

**Cons:**

- ❌ {Specific limitation}
- ❌ {Another limitation}

**Hero Angle Example**: "{Sample hero title}"

**Supporting Data**: {Key statistic that supports this angle}

---

### Option B: {Approach Name}

**Positioning**: {One sentence summary}

**Pros:**

- ✅ {Specific advantage}
- ✅ {Another advantage}
- ✅ {Third advantage}

**Cons:**

- ❌ {Specific limitation}
- ❌ {Another limitation}

**Hero Angle Example**: "{Sample hero title}"

**Supporting Data**: {Key statistic that supports this angle}

---

### Option C: {Approach Name}

**Positioning**: {One sentence summary}

**Pros:**

- ✅ {Specific advantage}
- ✅ {Another advantage}
- ✅ {Third advantage}

**Cons:**

- ❌ {Specific limitation}
- ❌ {Another limitation}

**Hero Angle Example**: "{Sample hero title}"

**Supporting Data**: {Key statistic that supports this angle}

---

## 💡 My Recommendation

**I recommend Option {A/B/C}** because:

1. {Reason based on research findings}
2. {Reason based on ICP pain points}
3. {Reason based on market positioning}

This approach will {explain expected outcome}.

---

**Please choose:**

- **A** - Use Option A as presented
- **B** - Use Option B as presented
- **C** - Use Option C as presented
- **Custom** - Describe your preferred direction (I'll adjust accordingly)

You can also request tweaks like:

- "Option A but emphasize {aspect} more"
- "Combine the {feature} from A with the {tone} from B"
- "All options miss {important point}, try this instead..."
```

**Wait for User Response**

The user may respond with:

1. **Letter choice** (A, B, or C) - Proceed with that option
2. **Modification request** - Adjust the chosen option based on feedback
3. **Custom direction** - Use their guidance to craft a hybrid or new approach
4. **Questions** - Answer and present refined options if needed

**Once user confirms direction:**

```
✅ Confirmed Direction: {Chosen approach}
{Any modifications requested}

Proceeding to craft the landing page with this strategic direction...
```

**Document the Decision**

Save the chosen direction for use in all copy sections:

- **Hero section** - Lead with this angle
- **Features** - Support this positioning
- **Testimonials** - Reinforce this message
- **FAQs** - Address objections to this approach
- **CTA** - Close with this value prop

### 6. Craft the Profile Copy

Use this structure (follow Profile interface in profilesData.ts):

#### Hero Section

- **Title**: Hook that speaks to their identity + main pain/aspiration
- **Description**:
  - Para 1: Quantified pain point with current market context
  - Para 2: How Warmstart transforms their situation (with metrics)
- **Image/Video**: Use existing video URL pattern
- **Responsive Config**: Consider mobile vs desktop visibility

#### Features Section (3 features)

Each feature should:

- Address a specific workflow pain point
- Show the "before" (current struggle)
- Demonstrate the "after" (Warmstart solution)
- Use their industry terminology
- Include specific use cases

**Structure:**

```typescript
{
  title: "Specific Capability/Outcome",
  description: [
    "Context paragraph: Their current struggle with specific details",
    "Solution paragraph: How Warmstart solves it with concrete examples"
  ],
  video: { url: "...", title: "..." }
}
```

#### Integrations Section

- **Title**: Focused on their existing workflow
- **Description**: Why integration matters to them
- **Features**: 3 integration benefits (LinkedIn, Gmail, CSV)
- **Tools**: What each tool monitors (ICP-specific)
- **Stats**: 2 compelling statistics from research

#### Testimonials

**For NEW Homepage Profiles:**
Create 3 full testimonials with realistic but illustrative examples:

- Author names (realistic for the ICP)
- Company names (fictitious but believable)
- Roles (appropriate for the ICP)
- Images (`/testimonial-avatar-1.jpg`, `-2.jpg`, `-3.jpg`)
- Image alt text (descriptive)
- Quotes (ICP-specific, following rules below)

**For UPDATED Homepage Profiles:**
**🚨 CRITICAL**: Do NOT modify existing testimonials. Keep the exact same:

- Author names
- Company names
- Roles
- Images
- Image alt text

Only modify the `quote` field if absolutely necessary to align with new positioning.

**Testimonial Writing Rules:**

- Make it specific (metrics, timelines, concrete outcomes)
- Include a "before" state (their struggle)
- Show the transformation
- End with quantified results
- Use authentic language (no marketing jargon)

**Note**: These are illustrative examples. Real customer testimonials should replace these as they become available.

#### CTA Section

- **Title**: Action-oriented question
- **Description**: Emotional close
- **Testimonial**: One testimonial quote (can be same as above)

#### FAQs (7-9 questions)

Must include:

1. "How does Warmstart help {ICP} specifically?"
2. "What are you doing with my email?" (standard privacy answer)
3. ICP-specific objections (3-4)
4. Pricing/ROI question
5. Integration questions

#### Keywords (10-15)

SEO keywords specific to:

- ICP job title variations
- Industry terms
- Pain point searches
- Solution searches
- Tool integrations

### 7. Copywriting Principles

**Voice & Tone:**

- ✅ Empathetic but not patronizing
- ✅ Data-driven but not clinical
- ✅ Aspirational but realistic
- ✅ Conversational but professional
- ❌ No hyperbole or exaggeration
- ❌ No generic marketing speak
- ❌ No unsubstantiated claims

**Structure:**

- Lead with pain/challenge (what they're experiencing)
- Quantify with research (validate their experience)
- Present solution (how Warmstart fits their workflow)
- Prove with specifics (concrete use cases)
- Call to action (clear next step)

**Language Patterns:**

- Use their industry terminology
- Mirror how they describe problems
- Cite current year data
- Include "you" language (second person)
- Paint specific scenarios

### 8. Responsive Configuration

Consider responsive needs:

```typescript
responsiveConfig?: {
  hideOnMobile?: ["hero" | "features" | "integrations" | "testimonials" | "cta" | "faqs"];
  hideOnDesktop?: ["hero" | "features" | "integrations" | "testimonials" | "cta" | "faqs"];
}
```

**When to use:**

- Hide complex features on mobile if they require detailed explanation
- Prioritize hero + CTA on mobile for conversion focus
- Keep FAQs visible on both (critical for objection handling)

### 9. Profile Naming Convention

```typescript
{
  name: "{ICP Display Name}", // e.g., "AI Founders", "Real Estate Agents"
  slug: "{url-slug}", // e.g., "ai-founders", "real-estate-agents"
  keywords: [...],
  hero: {...},
  // etc.
}
```

### 10. Quality Checklist

Before saving, verify:

- [ ] All statistics are sourced and current (2025 data when possible)
- [ ] Pain points match research findings
- [ ] Language mirrors how ICP describes their challenges
- [ ] Testimonials kept original author/company/role/image data
- [ ] Testimonial quotes are believable for that persona
- [ ] All 3 features address distinct workflow pain points
- [ ] Integration benefits are ICP-specific
- [ ] FAQs cover main objections
- [ ] Keywords match likely search queries
- [ ] Profile follows exact TypeScript interface
- [ ] Video URLs use existing pattern
- [ ] Responsive config considered (if needed)

### 11. File Location & Update Process

**File**: `src/app/(public)/(landing)/profilesData.ts`

**Update Process:**

1. Read existing file to preserve structure
2. If updating existing profile:
   - Find profile by slug
   - Replace entire profile object
   - Preserve array order
3. If creating new profile:
   - Add to end of profiles array (before closing `]`)
   - Maintain consistent formatting
4. Save the updated file
5. Proceed to validation (step 12)

### 12. Comprehensive Validation (CRITICAL)

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

**If failures**: Fix all ESLint issues before proceeding. Common issues:

- Trailing commas
- Quote style
- Line length
- Unused imports

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

**If failures**: Fix all TypeScript issues. Common issues:

- Missing properties in Profile interface
- Incorrect property types
- String vs string[] mismatches
- Missing required fields

#### Step 3: Test Validation

```
Use Task tool with general-purpose agent:
Task: "Run test suite with coverage"
Prompt: "Execute: pnpm test --run

Report:
- Total tests run
- Pass/fail count
- Any failing test names and reasons
- Exit code (must be 0)

Note: Ignore if no tests exist for profilesData.ts specifically.
"
```

**Success Criteria**: All tests pass OR no relevant tests exist

**If failures**:

- Check if tests validate profile structure
- Fix any broken tests caused by profile changes
- Ensure no regressions in existing profiles

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

This is the final validation - the build must complete successfully.
"
```

**Success Criteria**: Build completes successfully with exit code 0

**If failures**: This is critical - the page won't work in production. Common issues:

- TypeScript errors in build context
- Missing dependencies
- Import path issues
- Next.js compilation errors

#### Validation Summary Template

After ALL validations pass, show:

```
## ✅ Validation Complete

1. ESLint: ✅ PASSED (0 warnings, 0 errors)
2. TypeScript: ✅ PASSED (0 type errors)
3. Tests: ✅ PASSED (X tests, 0 failures)
4. Build: ✅ PASSED (completed in Xs)

**Status**: Ready for deployment
```

**If ANY validation fails**, you MUST:

1. Fix the issues
2. Re-run the failed validation step
3. Continue until ALL steps pass
4. DO NOT show final output until 100% validation success

### 13. Output Format

After completing the profile AND passing all validations, show:

```markdown
## ✅ {ICP Name} Profile Created/Updated

**Branch**: `{branch-name}`
**Slug**: `{slug}`
**Test URL**: `/{slug}`

### Key Research Insights Used:

- {Statistic 1 with source}
- {Statistic 2 with source}
- {Pain point 1}
- {Pain point 2}

### Content Highlights:

- **Hero**: {Brief description of angle}
- **Features**: {3 feature focus areas}
- **Stats**: {2 key statistics used}

### Validation Results:

✅ **ESLint**: Passed (0 warnings, 0 errors)
✅ **TypeScript**: Passed (0 type errors)
✅ **Tests**: Passed ({X} tests, 0 failures)
✅ **Build**: Passed (completed in {X}s)

### Next Steps:

1. Test the page locally at `/{slug}`
2. Review testimonials for authenticity
3. Verify all statistics are accurate
4. Check mobile responsiveness
5. Update images/videos if needed
6. Commit changes: `git add . && git commit -m "feat: add {ICP} landing page"`
7. Push branch: `git push origin {branch-name}`
8. Create PR for review
9. Deploy to production after PR approval

**Status**: ✅ Ready for Commit & PR
```

## Example Execution

```
User: "Create landing page for DevOps engineers at Series B startups"

You:
1. Ask clarifying questions (if needed)
2. Check current branch and ask user:
   "I'm ready to create the DevOps Engineers landing page.

   Which branch would you like me to work on?
   A) Create a new branch off main (recommended)
   B) Work on current branch: main

   Please choose A or B."

3. User chooses A → Create branch: landing-page/devops-engineers

4. Run 3-4 web searches on:
   - DevOps engineer challenges 2025
   - DevOps tooling adoption Series B
   - DevOps team collaboration pain points
   - DevOps sales enablement

5. Analyze research and identify insights

6. Present strategic direction options:
   "Based on my research, DevOps engineers at Series B struggle most with:
   - Tool sprawl (67% use 23+ tools)
   - Cross-team alignment (42% time in meetings)
   - Proving ROI to leadership

   Should we lead with:
   A) Tool consolidation pain
   B) Engineering-sales alignment gap
   C) ROI visibility and metrics

   Recommendation: Option B - alignment is unique differentiator"

7. User chooses: "B, but also emphasize the time savings metric"

8. Create profile with confirmed direction:
   - Hero: Engineering-sales alignment angle
   - Pain: Tool sprawl, cross-functional alignment, proving ROI
   - Language: "Pipeline", "CI/CD", "DevSecOps", "shift-left"
   - Stats: Tool adoption rates, time spent in meetings vs code
   - Features: Engineering-to-sales alignment, tool integration, metrics

9. Save to profilesData.ts

10. Run validation sequence via Task tool subagents:
   - ESLint fix & check → Pass
   - TypeScript → Pass
   - Tests → Pass
   - Build → Pass

11. Present summary with branch info and next steps
```

## Critical Reminders

🚨 **DO NOT**:

- Change existing testimonial names, companies, roles, or images
- Use generic marketing language
- Make claims without statistics
- Copy competitors' messaging
- Ignore the TypeScript interface structure
- Skip any validation steps
- Mark task complete without 100% validation success

✅ **DO**:

- Use 2025-specific research
- Mirror the ICP's language
- Quantify everything possible
- Make testimonials authentic and specific
- Follow the Profile interface exactly
- Consider responsive needs
- **ALWAYS run all 4 validation steps using Task tool subagents**
- Fix issues until ALL validations pass
- Only show final output after validation success

## Validation is Mandatory

**The command is NOT complete until:**

1. ✅ User confirms strategic direction (Step 5)
2. ✅ ESLint passes (0 warnings, 0 errors)
3. ✅ TypeScript passes (0 type errors)
4. ✅ Tests pass (0 failures)
5. ✅ Build passes (exit code 0)

**Use Task tool with general-purpose agent for validation steps.**

If any validation fails, FIX the issues and re-run. Do not proceed to next step until current step passes.

**Do not write any copy until user confirms strategic direction in Step 5.**

---

**Ready to create compelling, research-backed landing page copy with full validation!**
