# Fix Failing Tests

Systematically fix failing tests using proper debugging and testing patterns.

## Usage

```
/project:fix-failing-tests
```

## Steps

1. **Run test suite** - `pnpm test --run` to identify failing tests
2. **Analyze failures** - Review error messages and stack traces
3. **Check mocking patterns** - Reference `TESTING_STRATEGY.md` for proper mocking approaches
4. **Debug systematically**:
   - Run individual tests with `pnpm test --run <test-file>`
   - Use `pnpm test:ui` for interactive debugging
   - Check database mocking (avoid real databases in tests)
5. **Apply fixes** following these patterns:
   - Module-level mocking for external dependencies
   - Proper async/await handling
   - Type-safe test implementations
6. **Verify fixes** - Run full test suite to ensure no regressions
7. **Update coverage** - `pnpm test:coverage` to verify coverage remains high

Always follow the testing patterns documented in `TESTING_STRATEGY.md` and avoid common pitfalls like real database connections in tests.
