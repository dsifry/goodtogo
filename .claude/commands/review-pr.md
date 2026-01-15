# Review Pull Request

Conduct comprehensive code reviews using feedback from AI tools (CodeRabbit, Claude, etc.), human reviewers, and following Warmstart's review standards.

## Usage

```
/project:review-pr <pr-number>
```

## Review Process

### 1. Initial Assessment

- [ ] Read PR description and understand the context
- [ ] Check if PR follows conventional commit standards
- [ ] Verify all CI checks are passing
- [ ] Review linked issues and requirements

### 2. Code Review Checklist

#### Architecture & Design

- [ ] Changes follow existing architectural patterns
- [ ] Components placed in appropriate directories (`src/components/`, `src/hooks/`, etc.)
- [ ] Database changes follow schema conventions
- [ ] API routes follow REST patterns and response factory usage
- [ ] Background jobs properly integrated with job queue system

#### Code Quality

- [ ] Code is readable and well-structured
- [ ] Functions have single responsibility
- [ ] Complex logic is properly commented
- [ ] No hardcoded values (use constants or environment variables)
- [ ] Error handling is comprehensive
- [ ] TypeScript types are properly defined

#### Testing

- [ ] New features have corresponding tests
- [ ] Tests follow patterns from `TESTING_STRATEGY.md`
- [ ] Mock patterns are used correctly (no real database connections)
- [ ] Edge cases are covered
- [ ] Test coverage is maintained or improved

#### Security

- [ ] No sensitive information exposed (API keys, passwords)
- [ ] Input validation implemented
- [ ] Authentication/authorization properly handled
- [ ] SQL injection prevention (using Prisma properly)
- [ ] XSS prevention in React components

#### Performance

- [ ] No unnecessary re-renders in React components
- [ ] Database queries are optimized
- [ ] Large datasets handled efficiently
- [ ] Caching strategies implemented where appropriate
- [ ] No memory leaks in background jobs

#### Onboarding System (if applicable)

- [ ] Changes don't break 4-phase onboarding flow
- [ ] New features integrate with onboarding tours
- [ ] User state transitions are handled correctly
- [ ] Trial and subscription logic is preserved

### 3. AI Tool Integration

When AI tools provide feedback:

- [ ] Review all AI suggestions carefully
- [ ] Verify suggested changes align with project standards
- [ ] Address security and performance concerns raised
- [ ] Consider alternative solutions if AI suggestions don't fit

Common AI feedback patterns to watch for:

- Type safety improvements
- Performance optimizations
- Security vulnerabilities
- Code duplication
- Missing error handling

### 4. Human Review Integration

When reviewing alongside human feedback:

- [ ] Synthesize feedback from multiple reviewers
- [ ] Prioritize human domain expertise over AI suggestions
- [ ] Look for consensus between AI and human reviewers
- [ ] Address business logic concerns from human reviewers first

### 5. Providing Feedback

#### For Minor Issues

```markdown
**Suggestion**: Consider extracting this logic into a utility function for reusability.

**AI also suggested**: Similar refactoring for maintainability.
```

#### For Significant Issues

```markdown
**Issue**: This database query could cause performance problems with large datasets.

**Recommendation**: Add pagination or implement cursor-based pagination following our existing patterns in `src/hooks/queries/useContactsQuery.ts`.

**Security Concern**: Input validation missing for user-provided data.
```

#### For Architecture Concerns

```markdown
**Architecture Review**: This component doesn't follow our feature-based organization pattern.

**Suggestion**: Move to `src/components/campaign/` directory and split into smaller components following patterns in existing campaign components.

**Reference**: See `CLAUDE.md` documentation section on component patterns.
```

### 6. Approval Criteria

✅ **Approve when**:

- All feedback addressed satisfactorily
- CI checks passing
- Code follows project standards
- No security or performance red flags
- Documentation updated if needed

❌ **Request changes when**:

- Critical security issues
- Performance regressions
- Breaking changes without proper migration
- Tests failing or insufficient coverage
- Major architectural deviations

### 7. Follow-up Actions

- [ ] Verify changes are deployed successfully
- [ ] Monitor for any post-deployment issues
- [ ] Update documentation if new patterns introduced
- [ ] Consider adding to `.claude/commands/` if new workflow established
