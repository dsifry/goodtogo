# TDD Quick Reference

## The Iterative Workflow

### 1. Understand Requirements

- Ask user for clarification if unclear
- Write spec in `docs/todos/service_name/SERVICE_NAME_SPEC.md`
- Define interfaces before implementation

### 2. RED Phase (for each feature)

```bash
# Create test first
touch service.test.ts
pnpm test service.test.ts --run # Must fail - proves test works
```

### 3. GREEN Phase

```bash
# Minimal implementation to pass
touch service.ts
pnpm test service.test.ts --run # Must pass
```

### 4. REFACTOR Phase

```bash
# Improve code quality
pnpm test service.test.ts --watch # Stay green during refactoring
```

### 5. REPEAT for Next Feature

- Add test for edge case → RED
- Implement handling → GREEN
- Clean up code → REFACTOR
- Continue until all requirements covered

## Key Rules

- **Tests before code** - Always write test first
- **All tests must fail initially** - Proves test is valid
- **Minimum code to pass** - Don't over-engineer in GREEN
- **Refactor with green tests** - Safety net must pass
- **Use constructor DI always** - All dependencies injected
- **Mock all dependencies** - Use mock factories
- **Multiple cycles expected** - Build incrementally

## Anti-Patterns to Avoid

- ❌ Writing code before tests
- ❌ Skipping RED phase (test must fail first)
- ❌ Hardcoding dependencies
- ❌ Creating test data manually (use factories)
- ❌ Testing implementation details
- ❌ Trying to handle everything in one cycle

## TDD Cycle Checklist

For each new feature/requirement:

- [ ] Spec written/updated
- [ ] Test written
- [ ] Test fails (RED confirmed)
- [ ] Minimal code written
- [ ] Test passes (GREEN confirmed)
- [ ] Code refactored
- [ ] Tests still pass (REFACTOR confirmed)
- [ ] Coverage checked (aim for >80%)

## Example: Building a Service

```typescript
// CYCLE 1: Basic happy path
// 1. RED - Test the main functionality
it('should generate draft for contact', async () => {
  const result = await service.generateDraft(contact);
  expect(result.subject).toBeDefined();
}); // FAILS

// 2. GREEN - Just make it work
async generateDraft(contact) {
  return { subject: 'Draft' };
}

// 3. REFACTOR - Improve structure

// CYCLE 2: Handle missing data
// 1. RED - Test edge case
it('should handle contact without email', async () => {
  const contact = { ...mockContact, email: null };
  await expect(service.generateDraft(contact))
    .rejects.toThrow('Email required');
}); // FAILS

// 2. GREEN - Add validation
// 3. REFACTOR - Extract validation method

// CYCLE 3: Add caching
// ... continue cycles
```

Remember: Each cycle builds on the previous. Start simple, add complexity gradually.
