# TypeScript Patterns Guide

This guide contains TypeScript best practices, anti-patterns to avoid, and common patterns for the Warmstart codebase.

## Type Safety Best Practices

**🚨 CRITICAL**: NEVER use `as any` type casting. This is considered "lazy" and masks type errors instead of fixing them properly.

### TypeScript Anti-Patterns to Avoid

❌ **NEVER DO THESE**:

```typescript
// WRONG - Lazy type casting that masks errors
const data = someFunction() as any;
const result = (mockObject as any).someProperty;

// WRONG - Using @ts-ignore to suppress errors
// @ts-ignore
const badCode = problematicFunction();

// WRONG - Removing tests to fix type errors
// it.skip("test that has type issues", () => { ... });
```

✅ **DO THESE INSTEAD**:

```typescript
// CORRECT - Create proper interfaces
interface ExpectedData {
  property: string;
  value: number;
}
const data = someFunction() as ExpectedData;

// CORRECT - Use unknown as intermediary for complex casting
const result = (mockObject as unknown as ExpectedType).someProperty;

// CORRECT - Fix the root cause of type errors
const mockUser: Partial<User> = { id: "test", email: "test@example.com" };
```

## Common Type Patterns (Production Code)

### 1. Prisma JSON Fields

```typescript
// Correct - for database operations
// For DB "null" use Prisma.DbNull, for JSON sentinel use Prisma.JsonNull

// ▶ Example A – set column to DB NULL
processingError: Prisma.DbNull

// ▶ Example B – assign arbitrary JSON (e.g. error payload)
processingError: errorData as Prisma.InputJsonValue

// In interfaces
processingError?: Prisma.JsonValue | null;  // not string | null
```

### 2. Test File Type Patterns (⚠️ For tests only, not production code)

```typescript
// When fixing type errors in test files:

// ✅ CORRECT - Use unknown as intermediary
const mockUser = createMockUser() as unknown as User;
vi.mocked(someFunction).mockResolvedValue(result as unknown as ExpectedType);

// ❌ WRONG - Direct any casting
const mockUser = createMockUser() as any;

// For complex parameter types in tests:
const result = await someFunction(mockData as unknown as Parameters<typeof someFunction>[0]);
```

### 3. Null Safety Patterns

```typescript
// ❌ BAD - Will fail TypeScript strict null checks
if (contact.profileData?.score > 60) {
}

// ✅ GOOD - Extract value first, then check
const score = contact.profileData?.score;
if (score && score > 60) {
}
```

### 4. Index Signatures and Bracket Notation

```typescript
// LAST RESORT - When interface lacks index signature
(sanitized as unknown as Record<string, unknown>)[field] = value; // avoid if possible

// PREFERRED: Define typed helpers
function setField<T extends object>(obj: T, field: keyof T, value: T[keyof T]): void {
  obj[field] = value;
}

// Or extend type with index signature
type WithIndexSignature = ContactUpdateData & {
  [key: string]: unknown;
};
```

### 5. Test Mocking Patterns (Test Files Only)

```typescript
// Correct - use vi.mocked() with proper typing
const mockPrisma = createMock<PrismaClient>(); // using a typed mock factory
vi.mocked(PrismaClient).mockImplementation(() => mockPrisma);

// Alternative if no factory available
const mockPrisma: DeepMockProxy<PrismaClient> = mockDeep<PrismaClient>();
vi.mocked(PrismaClient).mockImplementation(() => mockPrisma);

// Avoid - direct any casting
(PrismaClient as any).mockImplementation(...);
vi.mocked(PrismaClient).mockImplementation(() => mockPrisma as any);
```

### 6. Set vs Array Type Handling

```typescript
// Internal processing
locations: Set<string>  // for deduplication

// External interfaces
locations: string[]  // for JSON serialization
```

## Null Safety Patterns

When dealing with TypeScript strict null checks:

```typescript
// ❌ WRONG - TypeScript can't track optional chaining in conditions
if (contact.processingResults?.salesIntelligence?.overallOpportunityScore > 60) {
  // Error: Object is possibly 'undefined'
}

// ✅ CORRECT - Extract value first
const opportunityScore = contact.processingResults?.salesIntelligence?.overallOpportunityScore;
if (opportunityScore && opportunityScore > 60) {
  // TypeScript knows opportunityScore is defined here
}

// ✅ ALSO CORRECT - For complex nested checks
const salesIntelligence = contact.processingResults?.salesIntelligence;
if (salesIntelligence?.overallOpportunityScore && salesIntelligence.overallOpportunityScore > 60) {
  // Works because we check the specific property
}
```

## Test-Specific Type Patterns

For test files, additional patterns apply:

### 1. Mock Return Types

```typescript
// Extract complex return types
type EmailHandlerResponse = Awaited<ReturnType<typeof emailHandler>>;

// Mock with proper typing
vi.mocked(emailHandler).mockResolvedValue({
  success: true,
} as EmailHandlerResponse);
```

### 2. Any Type Replacement in Tests

```typescript
// ❌ AVOID
const mockData = {
  /* ... */
} as any;

// ✅ PREFERRED - Cast through unknown
const mockData = {
  /* ... */
} as unknown as ExpectedType;

// ✅ BEST - Use proper typing from the start
const mockData: Partial<ExpectedType> = {
  /* ... */
};
```

### 3. Missing Mock Properties

```typescript
// When Prisma expects all properties, provide them
const mockContact: Contact = {
  id: "test-id",
  userId: "user-id",
  email: "test@example.com",
  // ... include ALL required properties
  // Use null for optional fields
  processingError: null,
  processingErrorUpdatedAt: null,
} as Contact;
```

### 4. Test Session Mocking

```typescript
// Use the createMockSession helper for consistent session mocking
import { createMockSession } from "@/test-utils/mock-session";

// Basic usage
const mockSession = createMockSession();

// With user overrides
const mockSession = createMockSession({
  user: { id: "custom-id", email: "custom@example.com" },
});

// With email account overrides
const mockSession = createMockSession({
  emailAccount: { lastSync: new Date("2024-06-01") },
});

// In test setup
let mockedSession: Session | null = null;

beforeEach(() => {
  mockedSession = createMockSession({ user: mockUser });
});
```

## Script Type Safety

When developing scripts, avoid `any` types:

```typescript
// ❌ AVOID
const data = JSON.parse(fs.readFileSync(file, "utf-8")) as any;

// ✅ PREFERRED - Define interfaces
interface ScriptData {
  contacts?: Contact[];
  // ... other properties
}
const data = JSON.parse(fs.readFileSync(file, "utf-8")) as ScriptData;

// ✅ ALSO GOOD - Type guard pattern
const rawData = JSON.parse(fs.readFileSync(file, "utf-8"));
const data = Array.isArray(rawData) ? rawData : rawData.contacts || [];
```

For null safety in scripts:

```typescript
// Extract nested values before comparisons
const score = contact.processingResults?.salesIntelligence?.overallOpportunityScore;
if (score && score > 60) {
  // Process high-score contact
}
```

## Build Error Resolution

When encountering build errors:

- **🚨 NEVER STOP PREMATURELY** - CONTINUE fixing ALL errors until the build succeeds completely
- **🚨 NEVER USE `as any` OR `@ts-ignore`** - These mask problems instead of solving them
- Don't stop at the first error - use `pnpm build 2>&1 | grep -E "Type error:|Error:"` to see all errors
- After fixing errors, always run the full build again to verify

### Systematic Error Fixing Process

1. **Identify ALL errors first**: Run full build and list every error
2. **Group errors by type**: TypeScript, ESLint, test failures
3. **Fix errors systematically**: Start with TypeScript, then ESLint, then tests
4. **Verify each fix**: Re-run build after each batch of fixes
5. **Never skip errors**: Every single error must be resolved

### Common patterns to remember

- Use `Prisma.JsonNull` instead of `null` for Prisma JSON fields
- Use `Prisma.InputJsonValue` for input, not `Prisma.JsonValue`
- Check property paths carefully (e.g., `profileData.person.positions` not `profileData.positions`)
- Extract nullable values before comparisons (see Null Safety Patterns)
- Create proper interfaces instead of using `any`

### Validation Sequence (repeat until ALL pass)

1. Fix all TypeScript errors: `pnpm tsc --noEmit`
2. Fix all ESLint warnings: `pnpm eslint <files> --max-warnings 0`
3. Run tests: `pnpm test --run`
4. Verify build: `pnpm build`
5. If ANY step fails, return to step 1

**Error Continuation Rule**: If you encounter 10 errors, fix ALL 10, not just the first 3

**Success Criteria**: Only mark task complete when build returns exit code 0 with zero errors

## Type Error Resolution

When fixing TypeScript errors:

- **ALWAYS** consult TypeScript Best Practices section above for proper patterns
- NEVER remove tests to fix type errors
- NEVER use `@ts-ignore` or suppress errors

## See Also

- @.claude/typescript-best-practices.md for additional patterns
- @docs/TESTING_STRATEGY.md section on "Never Remove Tests to Fix Type Errors"
