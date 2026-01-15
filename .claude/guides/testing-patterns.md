# Testing Patterns Guide

This guide contains testing best practices, anti-patterns to avoid, systematic approaches for the Warmstart codebase, and comprehensive documentation of our Test-Driven Development (TDD) process and mock factory patterns.

**Related Documents**:

- **Anti-Patterns Deep Dive**: @.claude/test-quality-anti-patterns.md - Detailed guide on what NOT to do
- **TypeScript Testing**: @.claude/guides/typescript-patterns.md#test-specific-type-patterns
- **Comprehensive Strategy**: @docs/TESTING_STRATEGY.md

## Testing Strategy

- **Vitest** for unit and integration tests
- Test files use `.test.ts` extension
- Coverage reports available via `pnpm test:coverage`
- Tests located in `src/lib/__tests__/` and component directories
- **Required Before Completion**: Always run tests with `pnpm test --run` after creating/modifying test files
  - The `--run` flag ensures the test process exits after completion (required for scripts)
  - For watching tests during development, omit the `--run` flag
- **Test Creation Pattern**: When implementing new features, create tests and verify they pass before marking the task complete
- **CRITICAL**: See @docs/TESTING_STRATEGY.md section on "Never Remove Tests to Fix Type Errors"

## Test-Driven Development (TDD) Process

### The Red-Green-Refactor Cycle

TDD follows a strict three-phase cycle that ensures code quality and comprehensive test coverage:

#### 1. RED Phase - Write a Failing Test

Write a test that describes the desired behavior BEFORE writing any implementation code:

```typescript
// Example: Testing a new needsRefresh method that doesn't exist yet
describe("SalesIntelligenceService.needsRefresh", () => {
  it("should return true when salesIntelligence is null", () => {
    const contact = createMockContact({ salesIntelligence: null });
    // This will FAIL because the method doesn't exist yet
    expect(SalesIntelligenceService.needsRefresh(contact)).toBe(true);
  });
});

// Run the test - it MUST fail
// ❌ Error: SalesIntelligenceService.needsRefresh is not a function
```

#### 2. GREEN Phase - Make the Test Pass

Write the MINIMUM code necessary to make the test pass:

```typescript
// Add to SalesIntelligenceService
static needsRefresh(contact: Contact): boolean {
  // Minimal implementation - just enough to pass
  return contact.salesIntelligence === null;
}

// Run the test again - it should pass
// ✅ Test passes
```

#### 3. REFACTOR Phase - Improve the Code

Now that the test passes, refactor to improve quality while keeping tests green:

```typescript
// Refactored with full logic
static needsRefresh(
  contact: Contact,
  options: RefreshOptions = {}
): boolean {
  // Early return for force refresh
  if (options.force) return true;

  // Check if never processed
  if (!contact.salesIntelligence) return true;

  // Check staleness
  const staleThreshold = options.staleAfterDays || 7;
  const lastAnalyzed = contact.salesIntelligenceUpdatedAt;
  if (!lastAnalyzed) return true;

  const daysSinceUpdate = differenceInDays(new Date(), lastAnalyzed);
  return daysSinceUpdate > staleThreshold;
}

// Run tests again - they should still pass
// ✅ All tests pass
```

### TDD Best Practices

1. **One Test at a Time**: Write one test, make it pass, then write the next
2. **Test First, Code Second**: NEVER write implementation before the test
3. **Keep Tests Simple**: Each test should verify ONE behavior
4. **Fast Feedback Loop**: Run tests continuously during development
5. **Refactor Under Green**: Only refactor when all tests are passing

### TDD Command Workflow

```bash
# 1. Create test file first
touch src/services/__tests__/my-service.test.ts

# 2. Write failing test
pnpm test my-service.test.ts --watch
# See it fail (RED)

# 3. Implement minimal code
# See test pass (GREEN)

# 4. Refactor if needed
# Keep tests passing (REFACTOR)

# 5. Commit when done
git add . && git commit -m "feat: implement MyService with TDD"
```

## Test Quality Management

**🚨 CRITICAL - Cascading Test Failure Anti-Pattern**:
When fixing one test causes another to fail, this usually indicates you're removing functionality instead of fixing the root cause.

❌ **WRONG - Symptom Masking**:

```typescript
// BAD - Removing detailed verification
expect(mockPrisma.$transaction).toHaveBeenCalledWith([
  expect.any(Promise), // ← Lost specificity!
  expect.any(Promise),
]);
```

✅ **CORRECT - Root Cause Fixing**:

```typescript
// GOOD - Fix mock setup while preserving verification
const filteredCountPromise = Promise.resolve(2);
const totalCountPromise = Promise.resolve(2);

mockPrisma.tag.count
  .mockReturnValueOnce(filteredCountPromise)
  .mockReturnValueOnce(totalCountPromise);

// Preserve detailed verification
expect(mockPrisma.$transaction).toHaveBeenCalledWith([
  filteredCountPromise, // ← Specific trackable promises
  totalCountPromise,
]);
```

## Systematic Test Review Process

**MANDATORY**: After fixing TypeScript or test errors, review ALL modified test files to ensure:

1. **Verification Logic Preserved**: Detailed `expect()` statements should remain specific
2. **Mock Setup Fixed**: Infrastructure issues resolved without removing test coverage
3. **Functionality Intact**: No test assertions were weakened or removed
4. **Root Cause Addressed**: Underlying type or mock issues fixed, not symptoms masked

**Review Pattern**:

```bash
# Get all modified test files
git diff --name-only | grep -E '\.test\.(ts|js|tsx|jsx)$'

# For each test file, check:
# 1. Are expect() statements still specific?
# 2. Were any assertions removed or weakened?
# 3. Are mocks properly set up?
# 4. Do tests still verify the same behavior?
```

## Mock Factory Patterns

### Overview of Mock Factories

Mock factories are centralized functions that create consistent, type-safe test data. They ensure all tests use properly structured data that matches our schemas while providing flexibility through overrides.

### Primary Mock Factory Locations

#### 1. Central Mock Factory Hub

**Location**: `src/lib/services/mock-factories.ts`
**Purpose**: Main repository for all domain model mock factories
**Exports**:

- `createMockContact()` - Creates Contact with all required fields
- `createMockSalesIntelligence()` - Creates complete SalesIntelligence objects
- `createMockConversationStarters()` - Creates ConversationStarters with sources
- `createMockConversationStarter()` - Single conversation starter
- `createMockLinkedInProfileData()` - LinkedIn profile structure
- `createMockLinkedInActivityData()` - LinkedIn activity with posts
- `createMockProcessingError()` - Error objects for testing error states
- `createMockProcessingResults()` - Processing results with timing data
- `createMockContactBatch()` - Generate multiple contacts for batch testing
- `MockScenarios` - Pre-configured scenarios (highOpportunity, withError, etc.)

#### 2. Test Utilities Directory

**Location**: `src/test-utils/`
**Purpose**: Specialized factories for specific testing needs

- **`mock-session.ts`**:
  - `createMockSession()` - NextAuth session objects
  - Used in API route testing and authentication tests

- **`linkedin-profile-factory.ts`**:
  - Detailed LinkedIn profile generation
  - Complex position and education structures

- **`extended-contact-factory.ts`**:
  - `createExtendedContact()` - Contact with embedded user data
  - Used for services requiring user context

- **`conversation-starter-factory.ts`**:
  - Specialized conversation starter generation
  - Source-specific starter creation

- **`location-factory.ts`**:
  - Geographic and location data mocks
  - Used in location-based features

- **`relationship-analysis-factory.ts`**:
  - Mock relationship analysis results
  - Connection strength calculations

#### 3. Domain-Specific Factories

**Location**: Various test directories

- **`src/lib/__tests__/factories/company-platform.factory.ts`**:
  - Company and platform-specific mocks
  - Industry and size variations

- **`src/run/process-contacts/__tests__/factories/`**:
  - Contact processing specific mocks
  - Bulk operation test data

### Using Mock Factories

#### Basic Usage

```typescript
import { createMockContact, createMockSalesIntelligence } from "@/lib/services/mock-factories";

// Create with defaults
const contact = createMockContact();

// Create with overrides
const customContact = createMockContact({
  name: "Jane Smith",
  email: "jane@example.com",
  salesIntelligence: createMockSalesIntelligence({
    overallOpportunityScore: 95,
  }),
});
```

#### Using Pre-built Scenarios

```typescript
import { MockScenarios } from "@/lib/services/mock-factories";

// High-value contact with recent activity
const hotLead = MockScenarios.highOpportunity();

// Contact with processing errors
const errorCase = MockScenarios.withError();

// Contact without LinkedIn data
const basicContact = MockScenarios.noLinkedIn();
```

#### Creating Test-Specific Factories

When you need a specialized factory for your tests:

```typescript
// In your test file or test/factories directory
function createMockCampaign(overrides: Partial<Campaign> = {}): Campaign {
  return {
    id: "campaign-123",
    name: "Test Campaign",
    status: "active",
    createdAt: new Date("2024-01-01"),
    userId: "user-123",
    ...overrides,
  };
}
```

### Factory Best Practices

1. **Always Use Factories**: Never create mock objects manually

   ```typescript
   // ❌ WRONG - Manual mock creation
   const contact = {
     id: "contact-1",
     email: "test@example.com",
     // Missing required fields!
   };

   // ✅ CORRECT - Use factory
   const contact = createMockContact({
     email: "test@example.com",
   });
   ```

2. **Compose Complex Objects**: Build from smaller factories

   ```typescript
   const contact = createMockContact({
     salesIntelligence: createMockSalesIntelligence({
       conversationStarters: createMockConversationStarters({
         recentAchievements: [
           createMockConversationStarter({
             context: "Custom achievement",
           }),
         ],
       }),
     }),
   });
   ```

3. **Use Type-Safe Overrides**: Let TypeScript catch errors

   ```typescript
   // TypeScript will catch invalid properties
   const contact = createMockContact({
     invalidField: "value", // ❌ TypeScript error
   });
   ```

4. **Create Scenario Helpers**: For common test cases

   ```typescript
   // Create reusable scenarios
   const createContactWithExpiredIntelligence = () => {
     const thirtyDaysAgo = new Date();
     thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

     return createMockContact({
       salesIntelligenceUpdatedAt: thirtyDaysAgo,
       salesIntelligence: createMockSalesIntelligence({
         lastAnalyzed: thirtyDaysAgo,
       }),
     });
   };
   ```

### When to Create New Factories

Create a new factory when:

1. **New Domain Model**: Adding a new schema/type to the system
2. **Complex Test Setup**: Repeated complex object creation in tests
3. **Specialized Scenarios**: Specific test scenarios used across files
4. **Integration Testing**: Need consistent data across multiple services

### Factory Organization Guidelines

1. **Central Factories** (`src/lib/services/mock-factories.ts`):
   - Core domain models (Contact, Campaign, User)
   - Widely used across tests
   - Schema-validated objects

2. **Test Utilities** (`src/test-utils/`):
   - Cross-cutting concerns (sessions, auth)
   - Test infrastructure (database mocks)
   - Specialized helpers

3. **Local Factories** (in test files):
   - Single-use mocks
   - Test-specific variations
   - Simple overrides

### Date Handling in Factories

All factories automatically handle date conversion:

```typescript
// Factories accept ISO strings but return Date objects
const contact = createMockContact({
  createdAt: "2024-01-01T00:00:00Z", // String input
});

console.log(contact.createdAt); // Date object
```

This is handled by the `JsonParserService` integration in mock factories.

## Test-Specific Type Patterns

For type patterns specific to test files, see @.claude/guides/typescript-patterns.md#test-specific-type-patterns

Key points:

- Use `unknown` as intermediary, not `any`
- Extract complex return types
- Provide all required mock properties
- Use `createMockSession` helper for sessions
- Always use mock factories for domain objects

## Testing Commands

- `pnpm test --run` - Run Vitest test suite and exit **[Use 240000ms timeout]**
- `pnpm test:coverage` - Generate test coverage reports **[Use 300000ms timeout]**
- `pnpm test --watch` - Run tests in watch mode (for interactive development)

## Testing & Debugging Tools

### Score and Draft Pipeline Testing

- `npx tsx scripts/test-score-and-draft-pipeline.ts --userEmail <email>` - Test full pipeline
- Add `--verbose` for full output, `--debug` for HTML/JSON, `--raw` for complete data
- Use `--no-cache` to fetch fresh LinkedIn data and regenerate sales intelligence
- Use `--raw-prompts` to see exact AI prompts being sent
- See @docs/TEST_SCORE_AND_DRAFT_PIPELINE.md for full details

## Test Organization

- Unit tests: Located next to the code they test
- Integration tests: In `src/lib/__tests__/`
- Component tests: In component directories
- E2E tests: In `tests/` directory (if applicable)

## Best Practices

1. **Test Creation**: Always create tests when implementing new features
2. **Test First**: Write tests before fixing bugs to ensure the bug is caught
3. **Mock Appropriately**: Mock external dependencies, not internal logic
4. **Test Behavior**: Test what the code does, not how it does it
5. **Keep Tests Simple**: Each test should verify one behavior
6. **Use Descriptive Names**: Test names should explain what is being tested

## Common Testing Patterns

### API Route Testing

```typescript
// Test API routes with proper session mocking
import { createMockSession } from "@/test-utils/mock-session";

it("should handle authenticated requests", async () => {
  const mockSession = createMockSession({ user: mockUser });
  // ... test implementation
});
```

### Component Testing

```typescript
// Test React components with proper context
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();
const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);
```

### Background Job Testing

```typescript
// Test job handlers with proper mocking
vi.mock("@/lib/prisma", () => ({
  prisma: mockPrisma,
}));

// Test the handler
await handler({ userId: "test-user" });
expect(mockPrisma.job.create).toHaveBeenCalled();
```

## See Also

- **@.claude/test-quality-anti-patterns.md** - Critical anti-patterns to avoid (MUST READ)
- **@docs/TESTING_STRATEGY.md** - Comprehensive testing documentation
- **@.claude/guides/typescript-patterns.md** - Test-specific type patterns
- **@docs/MOCK_FACTORIES_INVENTORY.md** - Complete inventory of mock factories
