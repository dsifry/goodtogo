# Add New Feature

Implement a new feature following Warmstart's architecture patterns and testing requirements.

## Usage

```
/project:add-feature <feature-name>
```

## Steps

1. **Plan the feature** - Use extended thinking to design the implementation
2. **Check existing patterns** - Look at similar features in the codebase
3. **Create database changes** - Update `prisma/schema.prisma` if needed
4. **Follow the architecture**:
   - API routes in `src/app/api/`
   - Components in `src/components/` (feature-based organization)
   - Hooks in `src/hooks/mutations/` and `src/hooks/queries/`
   - Background jobs in `src/run/` if needed
5. **Write tests** - Follow patterns from `TESTING_STRATEGY.md`
6. **Add analytics tracking** - Use PostHog tracking components
7. **Update documentation** - Add to relevant `.md` files
8. **Run checks**:
   - `pnpm lint`
   - `pnpm test --run`
   - `pnpm build`

Reference [instructions/prd.md](../../instructions/prd.md) for architectural guidance and [TESTING_STRATEGY.md](../../docs/TESTING_STRATEGY.md) for testing patterns.
