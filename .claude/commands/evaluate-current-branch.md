# evaluate-current-branch

Evaluates the current branch against main, analyzing merge impact, conflicts, and comprehensive changes using a multi-agent orchestration system.

## Usage

Type in chat: `/project:evaluate-current-branch [options]`

## Options

- `--verbose` - Include detailed file-by-file analysis
- `--metrics-only` - Show only quantitative metrics
- `--summary-only` - Show only executive summary
- `--include-tests` - Include test coverage analysis
- `--since <date>` - Analyze changes since specific date
- `--parallel-agents <n>` - Number of parallel agents (default: 10)
- `--model-strategy <auto|cost|performance>` - Model selection strategy (default: auto)
- `--skip-merge-analysis` - Skip merge difficulty analysis
- `--base-branch <branch>` - Compare against branch other than main (default: main)
- `--cost-limit <amount>` - Maximum spend for evaluation (default: $5.00)
- `--focus <area>` - Focus area: security|performance|compliance|financial (default: all)
- `--risk-tolerance <level>` - Risk threshold: low|medium|high (default: medium)
- `--business-context <file>` - Load business metrics and constraints
- `--stakeholder-report <type>` - Generate report for: board|engineering|customers|all (default: engineering)
- `--compliance-standards <list>` - Check compliance: SOC2,GDPR,HIPAA,PCI (comma-separated)
- `--customer-segment <segment>` - Analyze impact on: enterprise|smb|all (default: all)
- `--comprehensive` - **🎯 ULTIMATE ANALYSIS**: Performs complete deep analysis with ALL features enabled

## 🎯 Multi-Agent Architecture

This command uses a sophisticated multi-agent system with parallel processing and model specialization for optimal performance and cost efficiency.

### Agent Orchestration Pattern

```
┌─────────────────────────────────────────────┐
│      ORCHESTRATOR (Claude Opus 4.1)         │
│   - Task decomposition & prioritization     │
│   - Agent coordination & load balancing     │
│   - Result synthesis & validation           │
│   - Extended thinking mode (up to 4 hours)  │
└──────────┬──────────────────────────────────┘
           │ Phase 1: Parallel Data Collection (10 Primary Agents)
    ┌──────┴──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
    ▼             ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│Metrics  │ │Quality  │ │Security │ │Business │ │Customer │ │Infra    │ │  Risk   │ │  Merge  │ │  Docs   │ │Dev Prod │
│Analysis │ │& Tests  │ │Complianc│ │Financial│ │ Impact  │ │  Cost   │ │Assessor │ │Analyzer │ │Analysis │ │Analytics│
│(Haiku)  │ │(Sonnet4)│ │(Opus4.1)│ │(Opus4.1)│ │(Sonnet4)│ │(Sonnet4)│ │(Opus4.1)│ │(Opus4.1)│ │(Haiku)  │ │(Sonnet4)│
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
     │           │           │           │           │           │           │           │           │           │
     └───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
                                                    │
                        Phase 2: Executive Analysis & Decision Framework (After Phase 1)
                                                    ▼
                                    ┌────────────────────────────┐
                                    │    CTO DECISION ENGINE     │
                                    │      (Opus 4.1)            │
                                    │  Strategic Executive Review│
                                    └────────────┬───────────────┘
                                                 │
                                    Internal Sub-Agent Parallelization
                    ┌────────────────┬───────────┴────────────┬────────────────┬────────────────┐
                    ▼                ▼                        ▼                ▼                ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │  Tech Debt   │ │  Strategic   │ │   Business   │ │ Operational  │ │   Go/No-Go   │
            │  Calculator  │ │  Architect   │ │   Alignment  │ │  Readiness   │ │   Evaluator  │
            │ (Sonnet 4)   │ │  (Opus 4.1)  │ │  (Sonnet 4)  │ │  (Sonnet 4)  │ │  (Opus 4.1)  │
            └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### Model Specialization Strategy (Claude 4 Series - 2025)

#### **Claude Opus 4.1** - Advanced Reasoning & Multi-File Analysis

- **Primary Role**: Main orchestrator and complex multi-file reasoning
- **Key Capabilities**:
  - Extended thinking mode for deep analysis (can work for hours)
  - Multi-file code refactoring analysis (1 std deviation better than Opus 4)
  - Can handle thousands of steps in complex workflows
  - Hybrid reasoning with tool use during thinking
  - 72.5% on SWE-bench, 43.2% on Terminal-bench
- **Tasks**:
  - Task decomposition and planning with extended thinking
  - Agent coordination and dependency management
  - Risk assessment and architectural impact analysis
  - Final synthesis and executive summary generation
  - Complex pattern recognition across multiple files
  - Deep security and breaking change analysis

#### **Claude Sonnet 4** - Superior Code Analysis & Agentic Tasks

- **Primary Role**: Code analysis and feature classification
- **Key Capabilities**:
  - 72.7% on SWE-bench (world-class coding performance)
  - 1M token context window available
  - Hybrid reasoning modes (instant or extended thinking)
  - Excellent for sustained coding tasks
- **Tasks**:
  - Code quality assessment and TypeScript analysis
  - Feature and enhancement identification
  - Refactoring pattern detection
  - Test coverage and quality analysis
  - API contract and breaking change detection
  - Complex code understanding across large files

#### **Claude Opus 4.1** - Merge Complexity Analysis (New Agent)

- **Primary Role**: Analyze merge difficulty and conflict resolution
- **Key Capabilities**:
  - Conflict prediction and analysis
  - Semantic merge conflict detection
  - Branch divergence assessment
  - Integration complexity scoring
- **Tasks**:
  - Test merge simulation and conflict detection
  - Analyze conflicting changes semantically
  - Assess integration test requirements
  - Predict post-merge issues
  - Calculate merge difficulty score
  - Recommend merge strategies

#### **Claude 3.5 Haiku** - High-Speed Data Processing

- **Primary Role**: Metrics collection and simple analysis
- **Note**: Still using 3.5 Haiku as Claude 4 Haiku not yet released
- **Tasks**:
  - Git statistics and commit analysis
  - Line counting and file change metrics
  - Documentation parsing and summarization
  - TODO/FIXME comment extraction
  - Simple pattern matching and counting

#### **Claude Opus 4.1** - Strategic CTO Analysis (Phase 2 Agent)

- **Primary Role**: Executive-level strategic assessment and technical leadership review
- **Key Capabilities**:
  - Holistic system architecture evaluation
  - Technical debt quantification and prioritization
  - Strategic alignment assessment
  - Business impact analysis
  - Long-term maintainability projection
- **Dependencies**: Requires outputs from all Phase 1 agents (except Dev Productivity)
- **Internal Sub-Agents**:
  - **Tech Debt Analyzer (Sonnet 4)**: Quantifies and categorizes technical debt
  - **Strategic Architect (Opus 4.1)**: Evaluates architecture decisions and scalability
  - **Business Impact Assessor (Sonnet 4)**: Maps technical changes to business value
- **Outputs**:
  - Executive summary with strategic recommendations
  - Prioritized action items (Critical/Important/Nice-to-have)
  - Technical debt report with ROI calculations
  - Architecture quality assessment
  - Team productivity impact analysis

#### **Claude Sonnet 4** - Developer Productivity Analysis (Independent Agent)

- **Primary Role**: Analyze developer effort, productivity, and performance metrics
- **Key Capabilities**:
  - Work effort quantification (person-hours, complexity)
  - Historical baseline comparison (3-month lookback)
  - Industry benchmark comparison
  - Individual and team productivity metrics
  - DORA and SPACE framework analysis
- **Independence**: Runs in parallel but doesn't feed into CTO analysis
- **Metrics Analyzed**:
  - Lines of code written/modified/deleted
  - Commit frequency and size distribution
  - Code review turnaround time
  - Feature delivery velocity
  - Bug introduction rate
  - Refactoring vs new feature ratio
- **Comparisons**:
  - Against team's 3-month baseline
  - Against industry standards (DORA levels)
  - Against similar-sized branches
  - Individual contributor recognition
- **Outputs**:
  - Developer productivity scorecard
  - Effort analysis (person-hours invested)
  - Performance percentile rankings
  - Recognition highlights (exceptional work)
  - Areas for improvement (constructive feedback)

## 📊 Business Context Input

The command can load business context from a YAML/JSON file to inform financial and strategic analysis:

```yaml
# data/business-context.yaml
business_metrics:
  mrr: 250000 # Monthly Recurring Revenue
  arr: 3000000 # Annual Recurring Revenue
  customers:
    total: 450
    enterprise: 50
    smb: 300
    free: 100
  churn_rate: 2.5 # Percentage monthly
  nps_score: 42
  ltv: 48000 # Customer Lifetime Value
  cac: 12000 # Customer Acquisition Cost

financial_constraints:
  budget_remaining: 180000 # Q4 engineering budget
  headcount_available: 3 # Engineers available
  runway_months: 18
  burn_rate: 450000 # Monthly

compliance_requirements:
  soc2_audit: "2025-03-15"
  gdpr_review: "2025-02-01"
  hipaa_required: false
  pci_level: 2

market_position:
  main_competitors: ["CompetitorA", "CompetitorB"]
  feature_parity: 0.85 # 85% feature parity
  time_to_market_critical: true
  strategic_partnerships:
    - name: "PartnerCo"
      dependency: "high"
      sla_requirements: "99.95%"

board_priorities:
  q4_okrs:
    - "Reduce churn to <2%"
    - "Improve gross margin by 5%"
    - "Launch enterprise features"
  annual_goals:
    - "Achieve $5M ARR"
    - "500 customers"
    - "NPS > 50"

engineering_capacity:
  team_size: 12
  senior_engineers: 4
  current_velocity: 45 # Story points per sprint
  tech_debt_percentage: 35
  on_call_burden: "medium"
```

## What This Command Does

## 🚀 Parallel Agent Execution Framework

### Phase 0: Pre-Analysis & Branch Setup

**Critical Setup Steps** (Executed sequentially before agent dispatch):

```bash
# 1. Save current branch state
CURRENT_BRANCH=$(git branch --show-current)
git stash push -m "evaluate-branch-temp-stash"

# 2. Fetch latest main and analyze merge potential
git fetch origin main
git checkout main
git pull origin main

# 3. Collect main branch baseline metrics
MAIN_METRICS=$(git log --oneline | wc -l; cloc .)

# 4. Test merge without committing
git checkout $CURRENT_BRANCH
git merge-tree $(git merge-base HEAD main) main HEAD > merge_analysis.txt

# 5. Analyze divergence
COMMITS_AHEAD=$(git rev-list --count main..$CURRENT_BRANCH)
COMMITS_BEHIND=$(git rev-list --count $CURRENT_BRANCH..main)
```

### Phase 1: Orchestration & Task Distribution (Opus)

The **Orchestrator Agent** (Opus) performs initial analysis and creates a task execution plan:

```typescript
interface ExecutionPlan {
  currentBranch: string;
  baseBranch: string;
  mergeComplexity: MergeAnalysis;
  agents: Agent[];
  dependencies: DependencyGraph;
  parallelGroups: TaskGroup[];
  estimatedTime: number;
  modelAllocation: ModelStrategy;
}

interface MergeAnalysis {
  conflictCount: number;
  semanticConflicts: ConflictType[];
  divergenceMetrics: {
    commitsAhead: number;
    commitsBehind: number;
    divergenceScore: number;
  };
  mergeStrategy: "fast-forward" | "merge" | "rebase" | "squash";
}
```

### Phase 2: Parallel Agent Execution

#### **Agent Group A - Metrics Collection (3 Haiku Agents in Parallel)**

**Agent A1: Git Metrics Collector (Haiku)**

```bash
# Executes in parallel:
git fetch origin
git diff --stat origin/main
git log --oneline origin/main..HEAD
git shortlog -sn origin/main..HEAD
cloc . --git-diff-rel --git-diff-base=origin/main
```

**Agent A2: File Analysis Scanner (Haiku)**

```bash
# Executes in parallel:
find . -name "*.ts" -o -name "*.tsx" | xargs grep -c "any"
find . -name "*.test.ts" | wc -l
grep -r "TODO\|FIXME" --include="*.ts" --include="*.tsx"
```

**Agent A3: Dependency Analyzer (Haiku)**

```bash
# Executes in parallel:
npm list --depth=0 --json
npm audit --json
git diff origin/main package.json
```

#### **Agent Group B - Code Quality Analysis (2 Sonnet Agents in Parallel)**

**Agent B1: TypeScript & Testing Analyst (Sonnet)**

- Analyzes TypeScript improvements and type safety
- Evaluates test coverage and quality
- Identifies testing patterns and mock improvements
- Assesses code health indicators

**Agent B2: Feature & Refactoring Classifier (Sonnet)**

- Categorizes changes into features/fixes/refactoring
- Identifies architectural improvements
- Detects service modularization patterns
- Analyzes API changes and contracts

#### **Agent Group C - Complex Analysis (2 Opus 4.1 Agents)**

**Agent C1: Risk & Architecture Assessor (Opus 4.1)**

- Performs deep risk analysis
- Evaluates architectural impact
- Identifies breaking changes
- Assesses technical debt implications
- Analyzes security considerations

**Agent C2: Merge Complexity Analyzer (Opus 4.1)**

- Analyzes merge conflicts and resolution strategies
- Detects semantic conflicts beyond textual differences
- Assesses integration complexity
- Predicts post-merge test failures
- Recommends optimal merge strategy

### Phase 3: Strategic CTO Analysis (Sequential After Dependencies)

The **CTO Agent** (Opus 4.1) performs executive-level analysis using outputs from all Phase 2 agents:

**Internal Parallel Sub-Analysis**:

- Tech Debt Quantification (Sonnet 4)
- Architecture Assessment (Opus 4.1)
- Business Impact Mapping (Sonnet 4)

### Phase 4: Synthesis & Report Generation (Opus)

The **Orchestrator** collects all agent outputs including CTO strategic analysis and generates the final report.

## 📊 Agent Task Specifications

### Metrics Collection Agents (Haiku) - Fast, Parallel

**Why Haiku**: These tasks involve simple data extraction and counting that benefit from Haiku's speed without requiring complex reasoning.

```yaml
Agent_A1_Git_Metrics:
  model: claude-3.5-haiku
  timeout: 30s
  tasks:
    - branch_info: "git branch --show-current"
    - commit_count: "git rev-list --count origin/main..HEAD"
    - file_changes: "git diff --numstat origin/main"
    - author_stats: "git shortlog -sn origin/main..HEAD"
    - line_counts: "cloc . --git-diff-rel"
  output: structured_json

Agent_A2_File_Scanner:
  model: claude-3.5-haiku
  timeout: 30s
  tasks:
    - any_type_count: "grep 'any' usage in TypeScript files"
    - test_file_count: "count test files added/modified"
    - todo_extraction: "extract TODO/FIXME comments"
    - file_size_analysis: "identify large files"
  output: metrics_table

Agent_A3_Dependency_Analyzer:
  model: claude-3.5-haiku
  timeout: 30s
  tasks:
    - package_changes: "diff package.json dependencies"
    - security_audit: "npm audit results"
    - bundle_size: "analyze build output size"
    - new_dependencies: "list added packages"
  output: dependency_report
```

### Code Quality Agents (Sonnet 4) - Superior Code Understanding

**Why Sonnet 4**: With 72.7% on SWE-bench and hybrid reasoning capabilities, Sonnet 4 excels at understanding complex code patterns and sustained analysis tasks.

```yaml
Agent_B1_TypeScript_Analyst:
  model: claude-sonnet-4
  timeout: 60s
  reasoning_mode: instant # or 'extended' for deeper analysis
  tasks:
    - type_safety_improvements: "Analyze removed 'any' types and new interfaces"
    - test_quality_assessment: "Evaluate test coverage and mock patterns"
    - code_health_metrics: "ESLint fixes, complexity reduction"
    - null_safety_analysis: "Strict null check compliance"
  context_needed:
    - Changed TypeScript files
    - Test file modifications
    - ESLint configuration
  context_window: 1M # Can use up to 1M tokens
  output: quality_assessment

Agent_B2_Feature_Classifier:
  model: claude-sonnet-4
  timeout: 60s
  reasoning_mode: instant
  tasks:
    - feature_identification: "Identify new user-facing features"
    - enhancement_detection: "Find improvements to existing features"
    - refactoring_patterns: "Detect code structure improvements"
    - api_changes: "Identify API contract modifications"
  context_needed:
    - Changed source files
    - Commit messages
    - PR description
  output: feature_catalog
```

### Complex Analysis Agents (Opus 4.1) - Extended Multi-File Reasoning

**Why Opus 4.1**: With extended thinking mode and superior multi-file refactoring analysis, Opus 4.1 can handle thousands of steps and work continuously for hours on complex analysis.

```yaml
Agent_C1_Risk_Assessor:
  model: claude-opus-4.1
  timeout: 300s # Can work for hours if needed
  reasoning_mode: extended # Deep thinking with tool use
  tasks:
    - architectural_impact: "Analyze system-wide architectural changes"
    - risk_assessment: "Identify high-risk changes and regression potential"
    - breaking_changes: "Detect API/database schema breaking changes"
    - security_analysis: "Evaluate security implications"
    - technical_debt: "Assess debt reduction vs introduction"
    - multi_file_refactoring: "Analyze cross-file refactoring patterns"
  context_needed:
    - All agent outputs from Groups A & B
    - Critical path files
    - Database migrations
    - API definitions
  capabilities:
    - tool_use_during_thinking: true # Can use web search while analyzing
    - max_steps: 10000 # Can handle thousands of analysis steps
  output: comprehensive_risk_report

Agent_C2_Merge_Analyzer:
  model: claude-opus-4.1
  timeout: 180s
  reasoning_mode: extended
  tasks:
    - conflict_detection: "Run git merge-tree analysis"
    - semantic_conflicts: "Detect logical conflicts beyond textual"
    - integration_analysis: "Assess cross-service integration impact"
    - test_impact: "Predict which tests may fail post-merge"
    - strategy_recommendation: "Recommend merge vs rebase vs squash"
    - divergence_analysis: "Analyze branch divergence from main"
  context_needed:
    - Merge tree analysis output
    - Commits ahead/behind metrics
    - Modified file overlap analysis
    - Test file modifications
    - CI/CD configuration
  merge_specific_commands:
    - "git merge-tree $(git merge-base HEAD main) main HEAD"
    - "git diff --name-only main..HEAD | xargs -I {} git diff main HEAD -- {}"
    - "git log --oneline --graph main..HEAD"
    - "git rev-list --left-right --count main...HEAD"
  output: merge_complexity_report

Agent_C3_Security_Compliance:
  model: claude-opus-4.1
  timeout: 240s
  reasoning_mode: extended
  priority: CRITICAL
  tasks:
    - vulnerability_scanning: "Check all dependencies against CVE database"
    - secrets_detection: "Scan for API keys, passwords, tokens, certificates"
    - owasp_compliance: "Validate OWASP Top 10 compliance"
    - data_privacy: "GDPR/CCPA data handling verification"
    - compliance_standards: "SOC2, ISO27001, HIPAA control validation"
    - pen_test_simulation: "Assess attack surface changes"
    - supply_chain_security: "Verify dependency chain integrity"
  security_commands:
    - "npm audit --json"
    - "git diff main HEAD | grep -E '(api_key|password|secret|token|credential)'"
    - "trivy fs . --security-checks vuln,secret"
    - "semgrep --config=auto ."
  compliance_checks:
    - encryption_at_rest: "Verify data encryption standards"
    - encryption_in_transit: "Check TLS/SSL implementations"
    - access_controls: "Validate RBAC and authentication"
    - audit_logging: "Ensure compliance audit trails"
    - data_retention: "Verify retention policy compliance"
  output:
    security_score: "A-F rating"
    critical_vulnerabilities: []
    compliance_violations: []
    remediation_effort: "person-hours"
    legal_risk_exposure: "dollar amount"

Agent_C4_Business_Financial:
  model: claude-opus-4.1
  timeout: 180s
  reasoning_mode: extended
  business_context_required: true
  tasks:
    - revenue_impact_modeling: "Project MRR/ARR changes"
    - cost_benefit_analysis: "Calculate TCO and ROI"
    - market_timing_assessment: "Competitive advantage window"
    - customer_churn_risk: "Predict retention impact"
    - pricing_model_impact: "Assess pricing/packaging changes"
    - partner_ecosystem: "Third-party integration impacts"
  financial_calculations:
    - immediate_costs:
        development: "person-hours × $150"
        infrastructure: "cloud resource delta"
        support: "additional headcount needs"
        training: "documentation and education"
    - long_term_value:
        revenue_uplift: "new customer acquisition"
        churn_reduction: "retention improvement × CLV"
        operational_savings: "automation benefits"
        market_expansion: "new segment penetration"
    - key_metrics:
        roi: "(value - cost) / cost × 100"
        payback_period: "cost / monthly_benefit"
        npv: "3-year discounted cash flow"
        irr: "internal rate of return"
        break_even: "months to positive ROI"
  output:
    financial_summary:
      total_investment: "dollars"
      expected_return: "dollars"
      roi_percentage: "percent"
      payback_months: number
      risk_adjusted_npv: "dollars"
    revenue_impact:
      new_revenue: "monthly recurring"
      retention_improvement: "percentage"
      upsell_potential: "dollars"
    cost_breakdown:
      one_time: "dollars"
      recurring: "monthly"
      opportunity_cost: "dollars"

Agent_C5_Customer_Impact:
  model: claude-sonnet-4
  timeout: 120s
  reasoning_mode: instant
  tasks:
    - breaking_change_detection: "Identify customer-facing breaks"
    - migration_complexity: "Assess upgrade effort for customers"
    - ux_impact_analysis: "User experience improvements/degradations"
    - feature_adoption_prediction: "Likelihood of feature usage"
    - support_burden_projection: "Expected ticket volume"
    - customer_communication_needs: "Required notifications"
  customer_segments:
    enterprise:
      count: "number of accounts"
      revenue_percentage: "% of total"
      special_requirements: []
    smb:
      count: "number of accounts"
      revenue_percentage: "% of total"
      typical_usage_patterns: []
    free_tier:
      count: "number of users"
      conversion_potential: "percentage"
  impact_assessment:
    - affected_features: []
    - affected_workflows: []
    - required_migrations: []
    - downtime_requirements: "minutes"
    - rollback_complexity: "low|medium|high"
  output:
    customer_risk_score: 0-100
    affected_customers:
      total: number
      by_segment: {}
      revenue_at_risk: "dollars"
    migration_plan:
      auto_compatible: "percentage"
      requires_action: "percentage"
      breaking_changes: []
    support_projection:
      expected_tickets: number
      documentation_needs: []
      training_requirements: []
    satisfaction_impact:
      nps_change: "+/- points"
      churn_risk: "percentage"

Agent_C6_Infrastructure_Cost:
  model: claude-sonnet-4
  timeout: 90s
  reasoning_mode: instant
  tasks:
    - resource_utilization: "CPU, memory, storage projections"
    - scaling_requirements: "Auto-scaling and capacity needs"
    - cdn_bandwidth_impact: "Content delivery costs"
    - database_performance: "Query optimization and indexing"
    - api_rate_limits: "Third-party API usage changes"
    - monitoring_costs: "Logging, metrics, alerting expenses"
  infrastructure_analysis:
    compute:
      current_monthly: "dollars"
      projected_monthly: "dollars"
      delta: "dollars"
      optimization_opportunities: []
    storage:
      current_usage: "GB/TB"
      projected_usage: "GB/TB"
      cost_delta: "dollars"
    network:
      bandwidth_usage: "GB/month"
      cdn_costs: "dollars"
      api_calls: "millions/month"
    database:
      connection_pool: "size changes"
      query_performance: "ms improvements"
      index_requirements: []
      backup_size: "GB delta"
  third_party_services:
    - service_name: "provider"
      current_cost: "monthly"
      projected_cost: "monthly"
      api_limit_risk: "low|medium|high"
  output:
    monthly_cost_delta: "dollars"
    annual_projection: "dollars"
    cost_optimization_opportunities: []
    scaling_recommendations: []
    vendor_risk_assessment: []
```

### Strategic CTO Agent (Opus 4.1) - Executive Analysis

**Why Opus 4.1**: Requires synthesis of all previous analyses with strategic thinking and business alignment perspective.

```yaml
Agent_D1_CTO_Decision_Engine:
  model: claude-opus-4.1
  timeout: 300s
  reasoning_mode: extended
  execution_phase: 2 # Runs after all Phase 1 agents complete

  dependencies:
    - metrics_summary (from Metrics Agent)
    - quality_assessment (from Quality Agent)
    - security_report (from Security Agent)
    - financial_analysis (from Business Agent)
    - customer_impact (from Customer Agent)
    - infrastructure_costs (from Infra Agent)
    - risk_report (from Risk Agent)
    - merge_complexity (from Merge Agent)

  internal_sub_agents:
    tech_debt_calculator:
      model: claude-sonnet-4
      tasks:
        - quantify_debt: "Calculate technical debt in person-hours"
        - categorize_debt: "Classify by type: design, code, test, documentation"
        - roi_analysis: "Cost of fixing vs cost of maintaining"
        - interest_calculation: "Project debt growth over 6, 12, 24 months"
        - payment_schedule: "Optimal debt reduction timeline"

    strategic_architect:
      model: claude-opus-4.1
      tasks:
        - architecture_quality: "SQALE rating and maintainability index"
        - scalability_assessment: "Can this handle 10x growth?"
        - security_posture: "OWASP compliance and vulnerability assessment"
        - performance_projection: "Latency and throughput implications"
        - modernization_alignment: "Cloud-native and microservices readiness"
        - disaster_recovery: "RTO/RPO impact assessment"

    business_alignment:
      model: claude-sonnet-4
      tasks:
        - okr_alignment: "Match to quarterly/annual OKRs"
        - competitive_analysis: "Market positioning impact"
        - innovation_score: "Technical innovation index"
        - talent_impact: "Hiring and retention effects"
        - partnership_readiness: "API/integration maturity"

    operational_readiness:
      model: claude-sonnet-4
      tasks:
        - deployment_planning: "Zero-downtime deployment strategy"
        - monitoring_setup: "Alerts, dashboards, SLOs"
        - runbook_updates: "Operational documentation"
        - training_needs: "Team education requirements"
        - support_preparation: "Customer support readiness"
        - rollback_strategy: "Emergency recovery plan"

    go_no_go_evaluator:
      model: claude-opus-4.1
      tasks:
        - hard_gates: "Evaluate non-negotiable criteria"
        - risk_scoring: "Comprehensive risk assessment"
        - benefit_validation: "Verify claimed benefits"
        - timing_analysis: "Market and internal timing"
        - alternative_evaluation: "Consider other approaches"
        - decision_confidence: "Statistical confidence level"

  cto_evaluation_criteria:
    - strategic_alignment: "Does this move us toward our technical vision?"
    - risk_tolerance: "Acceptable risk level for production?"
    - resource_efficiency: "ROI on engineering time invested?"
    - innovation_enablement: "Does this unlock new capabilities?"
    - competitive_advantage: "Market differentiation impact?"

  executive_decision_framework:
    go_criteria: # All must be true
      - security_score: ">= B"
      - roi: ">= 2x"
      - customer_breaking_changes: "none OR mitigated"
      - compliance_violations: "= 0"
      - team_capacity: "available"
      - market_timing: "favorable"

    no_go_triggers: # Any true = reject
      - critical_vulnerabilities: "> 0 unpatched"
      - revenue_at_risk: "> $100,000"
      - compliance_violations: "> 0 critical"
      - customer_data_loss_risk: "any"
      - legal_exposure: "> $50,000"
      - team_burnout_risk: "high"

    conditional_criteria: # Approve with conditions
      - technical_debt_increase: "< 20%"
      - test_coverage_decrease: "< 5%"
      - performance_degradation: "< 10%"
      - documentation_gaps: "addressed within sprint"

  output_format:
    executive_verdict:
      decision: "✅ APPROVE | ⚠️ CONDITIONAL | ❌ REJECT"
      confidence_level: "95% | 80% | 60%"
      key_rationale: "primary decision factors"
      board_ready_summary: "1-2 sentences for board"

    financial_summary:
      total_investment: "$XXX,XXX"
      expected_return: "$XXX,XXX"
      roi: "XX%"
      payback_period: "X months"
      npv_3_year: "$XXX,XXX"
      risk_adjusted_value: "$XXX,XXX"

    risk_matrix:
      critical_risks:
        - risk: "description"
          probability: "low|medium|high"
          impact: "$XXX,XXX or description"
          mitigation: "strategy"
          owner: "role/person"

    operational_readiness:
      deployment_ready: "yes|no"
      monitoring_configured: "yes|no"
      runbooks_updated: "yes|no"
      rollback_tested: "yes|no"
      support_trained: "yes|no"
      customer_comms_prepared: "yes|no"

    prioritized_actions:
      before_merge: # Must complete
        - action: "description"
          owner: "team/person"
          effort: "hours"
          deadline: "date"

      within_24_hours: # Post-merge immediate
        - action: "description"
          success_metric: "measurement"

      within_sprint: # Short-term follow-up
        - action: "description"
          business_value: "impact"

    technical_debt_report:
      current_debt_hours: number
      added_debt_hours: number
      removed_debt_hours: number
      net_change: number
      debt_ratio: percentage # debt hours / total development hours
      projected_interest: "hours over next quarter"

    architecture_scorecard:
      maintainability: "A-F"
      scalability: "A-F"
      security: "A-F"
      performance: "A-F"
      testability: "A-F"
      overall: "A-F"

    team_impact_assessment:
      onboarding_complexity: "low|medium|high"
      documentation_quality: "poor|adequate|good|excellent"
      knowledge_silos: []
      productivity_impact: "+X% or -X%"
```

### Developer Productivity Agent (Sonnet 4) - Performance Analytics

**Why Sonnet 4**: Excellent at analyzing patterns and metrics with balanced speed and intelligence.

```yaml
Agent_A4_Developer_Productivity:
  model: claude-sonnet-4
  timeout: 60s
  reasoning_mode: instant
  execution_phase: 1 # Runs in parallel with other Phase 1 agents
  independent: true # Doesn't feed into CTO analysis

  baseline_analysis:
    lookback_period: "3 months"
    comparison_branches: "all merged branches in period"

    historical_metrics:
      - avg_commits_per_day: "git log --since='3 months ago' --format='%ad' --date=short | uniq -c"
      - avg_lines_per_commit: "git log --since='3 months ago' --numstat"
      - avg_pr_size: "gh pr list --state merged --limit 100 --json additions,deletions"
      - avg_review_time: "gh pr list --state merged --json createdAt,mergedAt"
      - avg_bugs_per_kloc: "git log --grep='fix' --since='3 months ago'"

    team_baseline:
      - total_commits: number
      - total_lines_changed: number
      - avg_velocity: "features per sprint"
      - avg_complexity: "cyclomatic complexity trend"

  current_branch_metrics:
    effort_analysis:
      - total_hours: "commits * avg_hours_per_commit"
      - active_days: "unique commit days"
      - contributors: "unique authors"
      - collaboration_score: "co-authored commits / total"

    code_metrics:
      - gross_lines_written: "additions + modifications"
      - net_lines_added: "additions - deletions"
      - files_touched: "unique files modified"
      - test_to_code_ratio: "test lines / implementation lines"
      - documentation_ratio: "comment lines / code lines"

    complexity_analysis:
      - avg_commit_size: "lines changed / commits"
      - refactoring_percentage: "refactored lines / total lines"
      - new_feature_percentage: "new feature lines / total lines"
      - bug_fix_percentage: "bug fix lines / total lines"

  industry_comparison:
    dora_metrics:
      - deployment_frequency: "compare to Elite/High/Medium/Low"
      - lead_time: "first commit to merge-ready"
      - change_failure_rate: "bugs introduced / changes"
      - mttr: "bug fix time average"

    space_framework:
      - satisfaction: "inferred from commit messages sentiment"
      - performance: "features delivered vs planned"
      - activity: "commits, PRs, reviews per day"
      - communication: "PR discussions, review comments"
      - efficiency: "rework rate, blocked time"

    percentile_rankings:
      - vs_team_baseline: "0-100 percentile"
      - vs_industry_average: "0-100 percentile"
      - vs_similar_branches: "0-100 percentile"

  recognition_analysis:
    exceptional_work:
      - complex_refactoring: "Successfully refactored X critical files"
      - test_coverage_hero: "Added X% test coverage"
      - performance_optimizer: "Improved performance by X%"
      - bug_crusher: "Fixed X critical bugs"
      - documentation_champion: "Added X lines of documentation"

    productivity_highlights:
      - velocity: "Delivered X% faster than average"
      - quality: "X% fewer bugs than average"
      - collaboration: "Helped X other developers"
      - innovation: "Introduced X new patterns/tools"

  output_format:
    productivity_scorecard:
      overall_rating: "Exceptional|Above Average|Average|Below Average"
      percentile_rank: 0-100

    effort_summary:
      estimated_hours: number
      calendar_days: number
      contributors: []
      commits: number

    performance_metrics:
      lines_per_day: number
      commits_per_day: number
      features_delivered: number
      bugs_fixed: number
      tests_added: number

    comparative_analysis:
      vs_personal_average: "+X%"
      vs_team_average: "+X%"
      vs_industry_benchmark: "percentile"

    recognition:
      achievements: []
      strengths: []
      improvements: [] # Constructive feedback

    cost_analysis:
      estimated_cost: "hours * hourly_rate"
      roi: "value_delivered / cost"
      efficiency_score: "output / input"
```

## 🔄 Execution Flow & Parallelization

### Execution Timeline

```
Time →
T0    [Pre-Analysis: Branch Setup & Merge Tree Generation]
      ↓
T1    [Orchestrator: Task Planning & Distribution]
      ↓
T2    [═══ Phase 1: Group A (3 Haiku) ═══][═══ Group B (2 Sonnet) ═══][═══ C (2 Opus 4.1) ═══]
      ↓                           ↓                           ↓
T3    [Results Collection & Validation]
      ↓
T4    [═══ Phase 2: CTO Strategic Analysis ═══]
      │     ┌──────────┬──────────┐
      └─────▶ Tech Debt │ Architect│ Business
              (Sonnet4) │(Opus 4.1)│(Sonnet4)
      ↓
T5    [CTO Synthesis & Strategic Recommendations]
      ↓
T6    [Orchestrator: Final Report Generation with CTO Assessment]
      ↓
T7    [Final Report Delivery + Branch Restoration]
```

### Parallel Execution Benefits

1. **Speed**: 8-10x faster than sequential execution with 10 agents
2. **Cost Optimization**: Balanced model usage optimizes cost/quality
3. **Quality**: Opus 4.1 focuses on critical decisions and complex analysis
4. **Scalability**: Dynamic agent count based on branch size and focus area
5. **Reliability**: Fault tolerance with agent retry and fallback strategies

## 📈 Dynamic Model Selection Strategies

### Auto Strategy (Default)

```javascript
function selectModel(task) {
  if (task.complexity === "simple" && task.volume === "high") {
    return "haiku"; // Fast, cost-effective for simple tasks
  } else if (task.requiresCodeUnderstanding) {
    return "sonnet"; // Balanced for code analysis
  } else if (task.requiresDeepReasoning || task.isRiskAssessment) {
    return "opus"; // Complex reasoning and critical analysis
  }
}
```

### Cost-Optimized Strategy

- 70% Haiku, 25% Sonnet, 5% Opus
- Suitable for routine branch evaluations
- Total cost: ~$0.15-0.30 per evaluation

### Performance-Optimized Strategy

- 20% Haiku, 40% Sonnet, 40% Opus
- Suitable for critical release branches
- Total cost: ~$0.80-1.50 per evaluation

## 🎨 Agent Coordination Strategies

### Dependency Management

Agents can have dependencies on other agents' outputs:

```yaml
dependency_graph:
  orchestrator:
    depends_on: []
    provides: [task_plan, agent_assignments]

  metrics_agents:
    depends_on: [task_plan]
    provides: [raw_metrics, file_stats, dependencies]

  quality_agents:
    depends_on: [task_plan, raw_metrics]
    provides: [quality_assessment, feature_list]

  risk_agent:
    depends_on: [raw_metrics, quality_assessment, feature_list]
    provides: [risk_report, recommendations]

  synthesizer:
    depends_on: [ALL_AGENT_OUTPUTS]
    provides: [final_report]
```

### Error Handling & Fault Tolerance

```typescript
interface AgentFailureStrategy {
  retryPolicy: {
    maxRetries: 3;
    backoffMs: [1000, 2000, 4000];
  };
  fallbackModel: {
    haiku: "sonnet"; // If Haiku fails, upgrade to Sonnet
    sonnet: "opus"; // If Sonnet fails, upgrade to Opus
    opus: null; // No fallback for Opus
  };
  partialResultHandling: "continue" | "abort";
}
```

### Communication Protocol

Agents communicate through a structured message-passing system:

```typescript
interface AgentMessage {
  agentId: string;
  modelUsed: "haiku" | "sonnet" | "opus";
  taskType: string;
  status: "pending" | "running" | "completed" | "failed";
  startTime: Date;
  endTime?: Date;
  result?: any;
  error?: Error;
  tokensUsed: number;
  cost: number;
}
```

## 📊 Advanced Prompting Techniques

### Task Decomposition Prompt (Orchestrator - Opus 4.1)

```markdown
You are the orchestrator for a branch evaluation system using Claude 4 series models.
You have access to extended thinking mode for complex planning.

CONTEXT:

- Branch: {branch_name}
- Commits: {commit_count}
- Files changed: {file_count}
- Multi-file refactoring detected: {has_refactoring}

AVAILABLE AGENTS:

- 3 Haiku 3.5 agents (ultra-fast, simple tasks)
- 2 Sonnet 4 agents (72.7% SWE-bench, superior code understanding, 1M context)
- 1 Opus 4.1 agent (extended reasoning, multi-file analysis, can work for hours)

CAPABILITIES:

- Sonnet 4 and Opus 4.1 support hybrid reasoning (instant or extended thinking)
- Opus 4.1 excels at multi-file refactoring analysis
- All agents can use tools during extended thinking

TASK: Create a parallel execution plan that:

1. Maximizes parallelization
2. Uses extended thinking for complex multi-file analysis
3. Leverages Sonnet 4's superior coding capabilities
4. Minimizes total execution time while maximizing insight
5. Optimizes cost vs depth tradeoff

OUTPUT FORMAT:
{
"phase1": [parallel_tasks],
"phase2": [dependent_tasks],
"reasoning_modes": {
"agent_id": "instant|extended"
},
"estimatedTime": seconds,
"estimatedCost": dollars,
"extendedThinkingJustification": "why certain agents need extended mode"
}
```

### Specialized Agent Prompts (Claude 4 Series)

**Haiku 3.5 - Metrics Agent:**

```markdown
You are a fast metrics collector. Execute these commands and return structured data:
{commands}
Return ONLY JSON with metrics. No analysis needed.
Speed is your priority.
```

**Sonnet 4 - Code Quality Analyst (Instant Mode):**

```markdown
You are a code quality analyst powered by Claude Sonnet 4.
You have 72.7% accuracy on SWE-bench and access to 1M token context.

Review these TypeScript changes:
{file_diffs}

Using your superior code understanding, identify:

1. Type safety improvements (quantify removed 'any' types)
2. Test coverage changes (calculate delta)
3. Code health metrics (complexity, duplication)
4. Refactoring patterns across files

Be specific, quantitative, and leverage your full context window.
```

**Sonnet 4 - Feature Classifier (Extended Thinking Mode):**

```markdown
[EXTENDED THINKING MODE ENABLED]
You are Claude Sonnet 4 with extended reasoning capabilities.
Take time to deeply analyze the codebase changes.

Given the full changeset, perform multi-step reasoning to:

1. Identify all new features and their interdependencies
2. Trace feature implementation across multiple files
3. Detect subtle enhancements and their impact
4. Map API changes to consumer effects

Use tool calls during your analysis if needed for:

- Searching for usage patterns
- Checking documentation updates
- Validating test coverage

Think step-by-step through the entire codebase impact.
```

**Opus 4.1 - Advanced Risk Assessor (Extended Mode):**

```markdown
[EXTENDED THINKING MODE WITH MULTI-FILE ANALYSIS]
You are Claude Opus 4.1, capable of sustained analysis for hours.
You excel at multi-file refactoring analysis (1 std dev better than Opus 4).

Given:

- Metrics: {metrics_summary}
- Quality report: {quality_report}
- Features: {feature_list}
- Full file tree: {file_structure}
- Change graph: {dependency_graph}

Perform exhaustive multi-file analysis:

1. Trace refactoring patterns across entire codebase
2. Identify cascading effects of architectural changes
3. Detect subtle breaking changes in deeply nested dependencies
4. Analyze security implications across service boundaries
5. Assess technical debt migration patterns
6. Map regression risks through call chains

You may work for up to 1 hour if needed for complex branches.
Use web search during analysis for:

- Security vulnerability databases
- Best practice validations
- Performance benchmarks

Your analysis should cover thousands of decision points if necessary.
```

**Opus 4.1 - Merge Complexity Analyzer (Extended Mode):**

```markdown
[EXTENDED THINKING MODE FOR MERGE ANALYSIS]
You are Claude Opus 4.1 analyzing merge complexity between branches.

Given:

- Current branch: {current_branch}
- Target branch: main (latest)
- Commits ahead: {commits_ahead}
- Commits behind: {commits_behind}
- Merge tree output: {merge_tree_analysis}
- Modified files overlap: {file_overlap}

Perform comprehensive merge analysis:

1. CONFLICT DETECTION
   - Parse git merge-tree output for textual conflicts
   - Identify files with conflicts and conflict markers
   - Categorize conflicts by type (code, imports, dependencies)

2. SEMANTIC CONFLICT ANALYSIS
   - Detect logical conflicts that git can't see:
     - Same function modified differently
     - Incompatible API changes
     - Type definition mismatches
     - Test assumptions invalidated
   - Identify "silent" merge issues that compile but break functionality

3. INTEGRATION COMPLEXITY
   - Assess how changes interact with main's new code
   - Identify integration test requirements
   - Detect cross-service dependencies affected

4. MERGE STRATEGY RECOMMENDATION
   Score each strategy (0-100):
   - Fast-forward merge (if possible)
   - Regular merge (preserves history)
   - Squash merge (clean history)
   - Rebase (linear history)

   Consider:
   - Number of commits
   - Commit message quality
   - Feature completeness
   - Team preferences

5. DIFFICULTY SCORING
   Calculate merge difficulty (0-100):
   - 0-20: Trivial (no conflicts, small changes)
   - 21-40: Easy (minor conflicts, clear resolution)
   - 41-60: Moderate (some conflicts, needs attention)
   - 61-80: Hard (many conflicts, semantic issues)
   - 81-100: Very Hard (extensive conflicts, high risk)

6. POST-MERGE PREDICTIONS
   - Which tests are likely to fail
   - Performance impact areas
   - User-facing changes requiring documentation
   - Deployment considerations

OUTPUT FORMAT:
{
"merge_difficulty_score": 0-100,
"conflicts": {
"textual": [],
"semantic": []
},
"recommended_strategy": "merge|rebase|squash",
"integration_requirements": [],
"risk_areas": [],
"estimated_resolution_time": "hours"
}
```

**Opus 4.1 - Strategic CTO Evaluator (Phase 2 Extended Mode):**

```markdown
[EXTENDED THINKING MODE - EXECUTIVE STRATEGIC ANALYSIS]
You are Claude Opus 4.1 acting as an experienced CTO evaluating a branch for production readiness.

You have 20+ years of experience leading engineering teams and making strategic technical decisions.
Your evaluation should reflect modern CTO priorities for 2024-2025.

Given all Phase 1 analyses:

- Metrics: {metrics_summary}
- Quality: {quality_assessment}
- Features: {feature_catalog}
- Risk: {risk_report}
- Merge Complexity: {merge_complexity_report}
- Current vs Main comparison: {branch_divergence}

Perform comprehensive CTO-level evaluation:

1. STRATEGIC ALIGNMENT ASSESSMENT
   - Does this advance our technical vision?
   - Innovation vs maintenance balance
   - Competitive advantage implications
   - Time-to-market considerations

2. TECHNICAL DEBT EVALUATION
   Quantify in person-hours:
   - Debt removed (refactoring wins)
   - Debt added (shortcuts taken)
   - Debt interest (compounding complexity)
   - Break-even point calculation

   Categorize by type:
   - Design debt (architecture issues)
   - Code debt (implementation issues)
   - Test debt (coverage gaps)
   - Documentation debt (knowledge gaps)

3. ARCHITECTURE QUALITY SCORECARD
   Rate A-F using industry standards:
   - Maintainability (SQALE rating)
   - Scalability (10x growth readiness)
   - Security (OWASP compliance)
   - Performance (latency/throughput)
   - Testability (coverage & quality)

4. BUSINESS IMPACT ANALYSIS
   - Team velocity impact (+/- %)
   - Operational cost implications
   - Customer experience changes
   - Compliance/regulatory adherence
   - Market positioning effects

5. RISK-ADJUSTED RECOMMENDATIONS
   Prioritize by criticality:

   CRITICAL (Block merge):
   - Security vulnerabilities
   - Data loss risks
   - Compliance violations
   - Severe performance regressions

   IMPORTANT (Fix within sprint):
   - Technical debt hotspots
   - Missing test coverage
   - Documentation gaps
   - Code quality issues

   NICE-TO-HAVE (Backlog):
   - Optimization opportunities
   - Refactoring suggestions
   - Feature enhancements

6. TEAM & CULTURE IMPACT
   - Knowledge distribution (bus factor)
   - Onboarding complexity for new devs
   - Code review burden
   - Operational overhead changes

7. STRATEGIC VERDICT
   Provide clear executive decision:
   - ✅ APPROVE: Ready for production
   - ⚠️ CONDITIONAL: Approve with specific requirements
   - ❌ REJECT: Significant issues requiring rework

   Include:
   - Confidence level (High/Medium/Low)
   - Key risks and mitigations
   - Success metrics to track post-merge

Use your extended thinking to:

- Run internal cost-benefit analyses
- Project long-term implications (6, 12, 24 months)
- Consider second-order effects
- Evaluate alternative approaches

Your assessment should be what a CTO would present to:

- Engineering teams (technical details)
- Product managers (delivery impact)
- Executives (business implications)
- Board members (strategic value)

OUTPUT: Executive decision with supporting data and actionable recommendations.
```

**Sonnet 4 - Developer Productivity Analyzer:**

```markdown
You are Claude Sonnet 4 analyzing developer productivity and performance metrics.
Your analysis is independent and provides recognition/feedback separate from code quality.

Given:

- Current branch metrics: {branch_stats}
- 3-month team baseline: {historical_baseline}
- Industry benchmarks: {dora_space_standards}

Perform comprehensive productivity analysis:

1. EFFORT QUANTIFICATION
   Calculate actual work invested:
   - Total person-hours (use industry avg: 2-4 hours per commit)
   - Active development days
   - Number of contributors and their roles
   - Collaboration patterns (pair programming, reviews)

2. BASELINE COMPARISON (3 months)
   Compare against team's historical performance:
   - Average commits per day: {team_avg}
   - Average lines per commit: {team_avg}
   - Average PR size: {team_avg}
   - Average feature velocity: {team_avg}

   Calculate percentiles:
   - This branch ranks in Xth percentile of team output
   - Productivity index: (this branch / team average) \* 100

3. INDUSTRY BENCHMARKING
   DORA Metrics Classification:
   - Elite: Top 5% (deployment daily, lead time <1hr)
   - High: Top 20% (deployment weekly, lead time <1 day)
   - Medium: Top 50% (deployment monthly, lead time <1 week)
   - Low: Bottom 50% (deployment <monthly, lead time >1 week)

   SPACE Framework Score:
   - Satisfaction: Infer from commit message tone
   - Performance: Features delivered vs complexity
   - Activity: Commit frequency and consistency
   - Communication: PR description quality, review participation
   - Efficiency: Rework rate, time to merge

4. INDIVIDUAL RECOGNITION
   Identify exceptional contributions:

   🏆 ACHIEVEMENTS TO HIGHLIGHT:
   - Velocity Champion: Delivered X% faster than average
   - Quality Star: X% fewer bugs introduced
   - Test Coverage Hero: Added X% coverage
   - Refactoring Master: Cleaned up X lines of tech debt
   - Documentation Champion: Best documented code
   - Collaboration Leader: Most helpful reviews

   For each contributor:
   - Personal best comparisons
   - Growth trajectory (improving/stable/declining)
   - Unique strengths demonstrated

5. CONSTRUCTIVE ANALYSIS
   Provide balanced feedback:

   STRENGTHS:
   - What this developer/team does exceptionally well
   - Patterns that should be replicated

   OPPORTUNITIES:
   - Areas where small improvements yield big gains
   - Specific skills to develop
   - Process improvements to consider

   Note: Frame as growth opportunities, not criticism

6. COST-VALUE ANALYSIS
   Business perspective:
   - Estimated cost: hours \* $150/hour (industry avg)
   - Value delivered: features \* business impact
   - ROI: value / cost ratio
   - Efficiency score vs similar branches

7. COMPARATIVE RANKINGS
   Position this work in context:
   - vs Developer's last 5 branches: Xth percentile
   - vs Team's last 20 branches: Xth percentile
   - vs Industry (DORA): Level achieved
   - vs Similar complexity branches: Xth percentile

OUTPUT FORMAT:
{
"developer_rating": "🌟 Exceptional | 👍 Above Average | ✓ Solid Work | 📈 Room to Grow",
"percentile_rank": 0-100,
"effort_invested": {
"hours": X,
"days": Y,
"cost": "$Z"
},
"productivity_score": {
"vs_personal": "+X%",
"vs_team": "+X%",
"vs_industry": "Elite/High/Medium/Low"
},
"recognition": [
"🏆 Achievement 1",
"⭐ Achievement 2"
],
"growth_opportunities": [
"Constructive suggestion 1",
"Skill development area 2"
]
}

Remember: This is about recognizing human effort and providing constructive feedback,
separate from code quality. Be encouraging while honest.
```

## 📈 Performance Optimization Techniques

### 1. Adaptive Agent Scaling

```typescript
function determineAgentCount(branchSize: BranchMetrics): AgentConfig {
  if (branchSize.files < 50 && branchSize.commits < 10) {
    return { haiku: 2, sonnet: 1, opus: 1 }; // Small branch
  } else if (branchSize.files < 200 && branchSize.commits < 50) {
    return { haiku: 3, sonnet: 2, opus: 1 }; // Medium branch
  } else {
    return { haiku: 5, sonnet: 3, opus: 2 }; // Large branch
  }
}
```

### 2. Smart Caching Strategy

```typescript
interface CacheStrategy {
  gitMetrics: { ttl: 3600; key: "branch_name" }; // 1 hour
  dependencies: { ttl: 86400; key: "package_lock" }; // 24 hours
  testCoverage: { ttl: 1800; key: "test_hash" }; // 30 minutes
}
```

### 3. Progressive Enhancement

Start with fast agents and progressively add detail:

```
Phase 1: Quick Scan (Haiku) → 10 seconds
Phase 2: Detailed Analysis (Sonnet) → 30 seconds
Phase 3: Deep Insights (Opus) → 60 seconds
```

Users can stop at any phase for faster results.

## 🎯 Output Format & Reporting

### Executive Summary (Generated by Orchestrator - Opus 4.1)

```
═══════════════════════════════════════════════════════
BRANCH EVALUATION: feat/typescript-migration vs main
═══════════════════════════════════════════════════════
Evaluation Time: 55 seconds | Agents Used: 10 | Cost: $0.58
Models: Opus 4.1 (x3), Sonnet 4 (x4), Haiku 3.5 (x3)

🎯 CTO STRATEGIC VERDICT: ⚠️ CONDITIONAL APPROVAL
Confidence: HIGH | Strategic Alignment: 85% | Technical Debt: -120 hours net

🔀 MERGE READINESS ASSESSMENT
• Merge Difficulty: 35/100 (Easy-Moderate)
• Branch Status: 23 commits ahead, 5 commits behind main
• Conflicts: 3 textual, 2 semantic detected
• Recommended Strategy: Rebase then merge
• Estimated Resolution Time: 2-3 hours

📈 ARCHITECTURE SCORECARD
• Maintainability: B+ → A (improved)
• Scalability: B → B+ (slight improvement)
• Security: A (maintained)
• Performance: B → A- (significant improvement)
• Testability: C+ → A (major improvement)
• Overall: B+ → A- ⬆️

💰 TECHNICAL DEBT ANALYSIS
• Debt Removed: 180 person-hours
• Debt Added: 60 person-hours
• Net Reduction: 120 hours (savings: $18,000)
• ROI Break-even: 2.5 sprints
• 6-month Projection: Additional 40 hours saved

🏆 TOP ACHIEVEMENTS
1. Migrated 45 files to TypeScript (100% type safety)
2. Increased test coverage by 23.5%
3. Reduced bundle size by 15%
4. Reduced technical debt by 120 person-hours

📊 METRICS SUMMARY
• Changes: +12,456 / -8,234 lines across 127 files
• Type Safety: 0 'any' types remaining (removed 234)
• Test Coverage: 67% → 89% (+22%)
• Team Velocity Impact: +15% projected

🚨 CTO PRIORITY RECOMMENDATIONS

CRITICAL (Must fix before merge):
1. Security: Update auth.ts to patch CVE-2024-XXXX
   - Impact: HIGH | Effort: 2 hours
   - Resolution: Apply security patch from main

2. Performance: Fix N+1 query in UserService
   - Impact: HIGH | Effort: 4 hours
   - Resolution: Implement batch loading

IMPORTANT (Fix within next sprint):
1. Documentation: Update API docs for 47 consumers
   - Timeline: 3 days | Business Impact: Partner integration

2. Test Coverage: Add integration tests for new TypeScript services
   - Timeline: 1 week | Impact: Regression prevention

NICE-TO-HAVE (Backlog):
1. Further optimize bundle splitting
2. Add performance monitoring dashboards
3. Implement automated dependency updates

📋 STRATEGIC ASSESSMENT
• Innovation Impact: Enables modern tooling adoption
• Competitive Advantage: 15% faster feature delivery
• Team Morale: Improved DX scores anticipated
• Onboarding: Reduced from 2 weeks to 1 week
• Business Value: $180K annual savings projected
```

### Developer Productivity Report (Independent Analysis)

```
═══════════════════════════════════════════════════════
DEVELOPER PRODUCTIVITY ANALYSIS
═══════════════════════════════════════════════════════
Developer Rating: 🌟 EXCEPTIONAL WORK
Percentile Rank: 92nd (Top 8% of team)

📊 EFFORT INVESTED
• Estimated Hours: 120 person-hours
• Calendar Days: 15 days (8 hours/day average)
• Contributors: 2 developers (1 primary, 1 reviewer)
• Total Commits: 45 (3 per day average)
• Estimated Cost: $18,000 (@$150/hour)

⚡ PRODUCTIVITY METRICS
• Lines per Day: 830 (team avg: 520)
• Commits per Day: 3.0 (team avg: 2.2)
• Features Delivered: 5 major, 12 minor
• Bugs Fixed: 23 (while adding features!)
• Tests Added: 156 (exceptional coverage)

📈 COMPARATIVE PERFORMANCE
• vs Personal Average: +35% productivity
• vs Team 3-Month Baseline: +58% productivity
• vs Industry (DORA): HIGH Performer
• vs Similar Branches: 85th percentile

🏆 RECOGNITION & ACHIEVEMENTS
1. 🥇 Test Coverage Hero: Added 22% coverage (best in quarter)
2. ⚡ Velocity Champion: 35% faster than personal average
3. 🎯 Quality Star: Zero bugs introduced (rare achievement)
4. 📚 Documentation Leader: 450 lines of quality docs
5. 🔧 Refactoring Master: Eliminated 120 hours of tech debt

💪 STRENGTHS DEMONSTRATED
• Exceptional test discipline (156 new tests)
• Strong refactoring skills (45 files improved)
• Excellent commit hygiene (atomic, well-described)
• Proactive documentation (exceeded standards)

🌱 GROWTH OPPORTUNITIES
• Consider smaller, more frequent PRs (current avg: 276 lines)
• Explore automation for repetitive patterns observed
• Share refactoring techniques with team (teaching opportunity)

💰 BUSINESS VALUE
• ROI: 3.2x (value delivered / cost)
• Tech Debt Reduced: $18,000 worth
• Future Velocity Gain: +15% for team
• Quality Impact: Prevented ~5 production bugs

📊 HISTORICAL CONTEXT (3-Month Baseline)
Team Average per Branch:
• Commits: 28 | This Branch: 45 (+60%)
• Lines Changed: 3,200 | This Branch: 12,456 (+289%)
• Days to Complete: 21 | This Branch: 15 (-28%)
• Test Coverage Added: 5% | This Branch: 22% (+340%)

Industry Comparison (DORA Levels):
• Lead Time: 2 days (HIGH - top 20%)
• Deployment Frequency: Ready for daily (ELITE potential)
• Change Failure Rate: 0% (ELITE - top 5%)
• MTTR: N/A (no failures to recover from)

NOTE: This exceptional performance deserves recognition!
Consider for: quarterly awards, bonus consideration,
or public team acknowledgment.
```

### Parallel Execution Report

```
AGENT EXECUTION TIMELINE
────────────────────────────────────────────────
T+0s   [Orchestrator] Task distribution started
T+1s   [Haiku-1] Git metrics collection started
T+1s   [Haiku-2] File analysis started
T+1s   [Haiku-3] Dependency scan started
T+1s   [Sonnet-1] TypeScript analysis started
T+1s   [Sonnet-2] Feature classification started
T+1s   [Sonnet-3] Developer productivity started
T+8s   [Haiku-1] ✓ Completed (7s, $0.02)
T+9s   [Haiku-3] ✓ Completed (8s, $0.02)
T+10s  [Haiku-2] ✓ Completed (9s, $0.02)
T+15s  [Opus-1] Risk assessment started
T+15s  [Opus-2] Merge analysis started
T+22s  [Sonnet-3] ✓ Dev productivity done (21s, $0.06)
T+25s  [Sonnet-1] ✓ Completed (24s, $0.08)
T+28s  [Sonnet-2] ✓ Completed (27s, $0.08)
T+35s  [Opus-2] ✓ Merge complete (20s, $0.06)
T+45s  [Opus-1] ✓ Risk complete (30s, $0.06)
T+46s  [CTO Analysis] Started (awaiting dependencies)
T+55s  [CTO] ✓ Strategic analysis complete
T+58s  [Orchestrator] ✓ Final synthesis complete
────────────────────────────────────────────────
Total: 58s | Cost: $0.64 | Speedup: 6.8x
```

## 📡 Post-Deployment Monitoring Framework

### Automated Monitoring Plan

```yaml
post_deployment_monitoring:
  immediate_checks: # First hour
    - metric: "error_rate"
      baseline: "current"
      threshold: "+0.5%"
      alert: "PagerDuty"
    - metric: "response_time_p95"
      baseline: "48-hour avg"
      threshold: "+100ms"
      alert: "Slack"
    - metric: "successful_requests"
      baseline: "hourly avg"
      threshold: "-5%"
      alert: "Email"

  day_1_checks: # First 24 hours
    - customer_complaints: "< 5"
    - revenue_impact: "< -1%"
    - support_tickets: "< baseline + 20%"
    - api_errors: "< baseline + 10%"

  week_1_review:
    - performance_analysis: "Full latency distribution"
    - cost_analysis: "Infrastructure spend delta"
    - customer_feedback: "NPS pulse survey"
    - team_retrospective: "Lessons learned"

  month_1_validation:
    - roi_actual_vs_projected: "Variance analysis"
    - technical_debt_impact: "Velocity measurement"
    - customer_satisfaction: "Full NPS survey"
    - competitive_analysis: "Market response"

rollback_triggers:
  automatic: # System auto-rollback
    - error_rate: "> baseline + 2%"
    - revenue_drop: "> 3% hourly"
    - data_corruption: "any"
    - security_breach: "any"

  manual_review: # Human decision required
    - customer_complaints: "> 10"
    - performance_degradation: "> 20%"
    - cost_overrun: "> 50%"
    - partner_api_failures: "> 5%"

success_criteria:
  hour_1:
    - error_rate: "≤ baseline"
    - performance: "≤ baseline + 50ms"
    - revenue: "≥ baseline - 0.5%"

  day_1:
    - customer_satisfaction: "No significant complaints"
    - system_stability: "No P0/P1 incidents"
    - team_confidence: "Positive feedback"

  week_1:
    - adoption_rate: "> 30% for new features"
    - performance_gains: "Measured and validated"
    - cost_efficiency: "Within projections"
```

### Monitoring Dashboard Configuration

```yaml
dashboards:
  executive_dashboard:
    widgets:
      - revenue_impact: "Real-time MRR tracker"
      - customer_health: "Churn risk indicator"
      - system_health: "Overall status"
      - roi_tracker: "Actual vs projected"

  technical_dashboard:
    widgets:
      - error_rates: "By service and endpoint"
      - latency_heatmap: "P50, P95, P99"
      - infrastructure_costs: "Real-time spend"
      - deployment_status: "Rollout progress"

  customer_dashboard:
    widgets:
      - support_tickets: "Volume and sentiment"
      - feature_adoption: "Usage metrics"
      - satisfaction_score: "Real-time NPS"
      - migration_status: "Customer upgrades"
```

## 📢 Stakeholder Communication Templates

### Board Executive Summary

```markdown
# Branch Evaluation: Board Summary

**Date**: [Date]
**Branch**: [Branch Name]
**Decision**: ✅ APPROVED / ⚠️ CONDITIONAL / ❌ REJECTED

## Strategic Impact

**Business Value**: [1-2 sentences on revenue/competitive impact]
**Investment**: $[XXX]K with [X] month payback
**Risk Level**: LOW / MEDIUM / HIGH with mitigation plan

## Key Metrics

- **ROI**: [X]x return expected
- **Customer Impact**: [Positive/Neutral/Managed]
- **Market Timing**: [Favorable/Neutral/Challenging]

## Recommendation

[1 sentence clear recommendation with confidence level]

## Next Steps

1. [Immediate action if approved]
2. [Success metrics to track]
```

### Engineering Team Brief

```markdown
# Technical Evaluation Report

**Branch**: [Branch Name]
**Lead Developer**: [Name]
**Review Date**: [Date]

## Technical Assessment

### Achievements ✅

- [Key technical improvements]
- [Performance gains]
- [Debt reduction]

### Architecture Changes

- **Scalability**: [Impact]
- **Maintainability**: [Grade change]
- **Security**: [Improvements]

### Action Items

#### Before Merge

- [ ] [Critical fix with owner]
- [ ] [Security patch]

#### Post-Merge

- [ ] [Monitoring setup]
- [ ] [Documentation update]

## Deployment Plan

- **Strategy**: [Blue-green/Canary/Rolling]
- **Rollback Time**: [X minutes]
- **Risk Level**: [Low/Medium/High]
```

### Customer Communication

```markdown
# Product Update Notification

## What's New

We're excited to announce improvements to [feature/area]:

- ✨ [Key benefit 1]
- 🚀 [Performance improvement]
- 🔒 [Security enhancement]

## What You Need to Know

- **When**: [Deployment date/time]
- **Impact**: [None/Minimal/Action Required]
- **Duration**: [Expected timeline]

## Action Required (if applicable)

1. [Specific step customers must take]
2. [Migration deadline if any]

## Support Resources

- 📚 [Documentation link]
- 💬 [Support channel]
- 📧 [Contact email]

## Questions?

Our team is ready to help. Contact [support channel].
```

### Investor Update

```markdown
# Technical Development Update

## Executive Summary

**Quarter**: Q[X] 2025
**Development Efficiency**: [X]% improvement
**Technical Debt**: Reduced by [X] hours

## Strategic Technology Investments

### Completed This Period

- [Major technical achievement]
- ROI: [X]x on engineering investment
- Customer Impact: [Metric improvement]

### Innovation Metrics

- **Deployment Frequency**: [X] per day (↑ X%)
- **Lead Time**: [X] hours (↓ X%)
- **System Reliability**: [X]% uptime
- **Security Posture**: [Grade/Score]

## Competitive Advantage

[How technical improvements strengthen market position]

## Forward Looking

[Technical roadmap alignment with business goals]
```

### Internal Incident Response

```markdown
# Deployment Status Report

**Status**: 🟢 GREEN / 🟡 YELLOW / 🔴 RED
**Time**: [Timestamp]
**Incident Commander**: [Name]

## Current State

- **Deployment Progress**: [X]% complete
- **Error Rate**: [Current vs Baseline]
- **Customer Impact**: [None/Minor/Major]

## Metrics

| Metric      | Baseline | Current | Status     |
| ----------- | -------- | ------- | ---------- |
| Errors      | 0.1%     | [X]%    | [✅/⚠️/❌] |
| Latency P95 | 200ms    | [X]ms   | [✅/⚠️/❌] |
| Revenue     | $[X]/hr  | $[X]/hr | [✅/⚠️/❌] |

## Actions Taken

1. [Action with timestamp]
2. [Mitigation applied]

## Next Steps

- [ ] [Immediate action]
- [ ] [Follow-up required]

## Rollback Decision

**Recommendation**: [Continue/Monitor/Rollback]
**Rationale**: [Clear reasoning]
```

## 🚀 Implementation Guide

### Step 1: Install Dependencies

```bash
# Ensure cloc is installed
brew install cloc || apt-get install cloc

# Verify git is configured
git config --get remote.origin.url
```

### Step 2: Configure Agent System

```typescript
// .claude/config/agents.json
{
  "agents": {
    "orchestrator": {
      "model": "claude-opus-4.1",
      "reasoning_mode": "extended",
      "timeout": 180000
    },
    "metrics": {
      "count": 3,
      "model": "claude-3.5-haiku",
      "timeout": 30000
    },
    "quality": {
      "count": 2,
      "model": "claude-sonnet-4",
      "reasoning_mode": "instant",
      "context_window": "1M",
      "timeout": 60000
    },
    "risk": {
      "count": 1,
      "model": "claude-opus-4.1",
      "reasoning_mode": "extended",
      "timeout": 300000,
      "capabilities": {
        "tool_use_during_thinking": true,
        "max_steps": 10000
      }
    }
  },
  "parallelization": {
    "maxConcurrent": 6,
    "queueStrategy": "priority"
  },
  "model_versions": {
    "opus": "4.1",
    "sonnet": "4.0",
    "haiku": "3.5"
  }
}
```

### Step 3: Execute Command

```bash
# Basic parallel evaluation
/project:evaluate-current-branch

# With specific model strategy
/project:evaluate-current-branch --model-strategy performance

# With custom parallelization
/project:evaluate-current-branch --parallel-agents 8
```

## 📚 Best Practices

1. **Task Granularity**: Keep individual agent tasks focused and atomic
2. **Context Sharing**: Minimize context passed between agents to reduce token usage
3. **Progressive Detail**: Start with quick overview, add detail on demand
4. **Error Recovery**: Design for partial failures with graceful degradation
5. **Cost Monitoring**: Track token usage per agent for optimization
6. **Result Validation**: Cross-check agent outputs for consistency

## 🔍 Troubleshooting

### Common Issues

**Agent Timeout**

- Increase timeout for complex branches
- Reduce task scope per agent
- Consider upgrading model (Haiku → Sonnet)

**High Costs**

- Use cost-optimized strategy
- Cache repeated analyses
- Reduce Opus usage for routine evaluations

**Inconsistent Results**

- Add validation agent
- Increase temperature for creative tasks
- Decrease temperature for metrics

## 📁 Report Output and File Saving

### Automatic Report Generation

The evaluation automatically saves ALL outputs to `data/[date]-[branch]/` directory structure:

```bash
# Complete evaluation data structure
data/
└── 2025-08-23-feat-typescript-score-and-draft-migration/
    ├── executive-summary.md          # 2-3 page CEO/Board summary
    ├── detailed-report.md            # Full detailed report (10-20 pages)
    ├── wip/                          # Work-in-progress intermediate data
    │   ├── 01-orchestrator-plan.json      # Initial task distribution
    │   ├── 02-metrics-agent.json          # Git metrics (Haiku)
    │   ├── 03-file-scanner-agent.json     # File analysis (Haiku)
    │   ├── 04-dependency-agent.json       # Dependency scan (Haiku)
    │   ├── 05-typescript-analyst.json     # TypeScript analysis (Sonnet)
    │   ├── 06-feature-classifier.json     # Feature detection (Sonnet)
    │   ├── 07-risk-assessor.json          # Risk analysis (Opus)
    │   ├── 08-merge-analyzer.json         # Merge complexity (Opus)
    │   ├── 09-security-compliance.json    # Security scan (Opus)
    │   ├── 10-business-financial.json     # Financial modeling (Opus)
    │   ├── 11-customer-impact.json        # Customer analysis (Sonnet)
    │   ├── 12-infrastructure-cost.json    # Infra costs (Sonnet)
    │   ├── 13-developer-productivity.json # Dev metrics (Sonnet)
    │   ├── 14-cto-strategic.json          # CTO analysis (Opus)
    │   └── 15-final-synthesis.json        # Orchestrator final
    ├── raw-data/                     # Raw unprocessed data
    │   ├── git-stats.txt                  # Raw git output
    │   ├── file-changes.diff              # Complete diff
    │   ├── dependency-audit.json          # npm audit results
    │   └── merge-tree.txt                 # Merge analysis
    └── metadata.json                 # Evaluation metadata
```

### Data Persistence Strategy

**CRITICAL**: All intermediate agent outputs MUST be saved immediately after generation:

```typescript
// Save intermediate data as each agent completes
async function saveAgentOutput(agentId: string, data: any, branch: string) {
  const date = new Date().toISOString().split("T")[0];
  const cleanBranch = branch.replace(/[^a-zA-Z0-9-]/g, "-");
  const dir = `data/${date}-${cleanBranch}/wip/`;

  // Ensure directory exists
  await fs.mkdir(dir, { recursive: true });

  // Save with numbered prefix for execution order
  const filename = `${dir}${agentId.padStart(2, "0")}-${data.agentName}.json`;
  await fs.writeFile(filename, JSON.stringify(data, null, 2));

  console.log(`💾 Saved: ${filename}`);
  return filename;
}

// Example usage in agent execution
async function executeAgent(agent: Agent, context: Context) {
  console.log(`🚀 Starting ${agent.name}...`);

  // Execute agent task
  const result = await agent.execute(context);

  // IMMEDIATELY save the output
  const savedPath = await saveAgentOutput(
    agent.id,
    {
      agentName: agent.name,
      model: agent.model,
      timestamp: new Date().toISOString(),
      result: result,
      tokensUsed: result.tokensUsed,
      executionTime: result.executionTime,
    },
    context.branch
  );

  console.log(`✅ ${agent.name} complete, saved to ${savedPath}`);
  return result;
}
```

### Why Intermediate Data Storage is Critical

1. **Debugging**: Can review exact agent outputs when issues occur
2. **Audit Trail**: Complete record of decision-making process
3. **Resume Capability**: Can restart from any point if interrupted
4. **Cost Tracking**: Monitor token usage per agent
5. **Performance Analysis**: Identify slow agents for optimization
6. **Learning**: Build dataset for future model improvements

### Main Branch Caching

The system intelligently caches main branch evaluations to avoid redundant analysis:

```bash
# Cache structure in /data/ directory (gitignored)
/data/
└── branch-evaluations/
    └── main-branch-cache/
        ├── main-2025-08-22-14-30-abc123f.json  # Full analysis cache
        ├── main-2025-08-22-14-30-abc123f.meta  # Metadata (commit hash, timestamp)
        └── main-2025-08-22-14-30-abc123f.lock  # Lock file during analysis
```

#### Cache Logic

```bash
# The command automatically:
1. Checks current main branch commit hash
2. Looks for existing cache with matching hash
3. If found and < 7 days old: reuses cached analysis
4. If not found or stale: runs fresh analysis and caches
5. Compares current branch against cached baseline

# Cache invalidation triggers:
- Main branch has new commits
- Cache file is > 7 days old
- --force-refresh flag is used
- Cache file is corrupted/incomplete
```

#### Cache Validation Flow

```typescript
// Pseudocode for cache validation
async function validateMainBranchCache() {
  // 1. Get current main branch commit
  const mainCommit = await git.revParse("main");

  // 2. Look for matching cache file
  const cachePattern = `/data/branch-evaluations/main-branch-cache/main-*-${mainCommit}.json`;
  const cacheFiles = glob(cachePattern);

  if (cacheFiles.length === 0) {
    console.log("❌ No cache found for main@" + mainCommit);
    return null;
  }

  // 3. Check cache age
  const cacheFile = cacheFiles[0];
  const cacheAge = Date.now() - fs.statSync(cacheFile).mtime;
  const sevenDays = 7 * 24 * 60 * 60 * 1000;

  if (cacheAge > sevenDays) {
    console.log("⏰ Cache expired (age: " + formatDuration(cacheAge) + ")");
    return null;
  }

  // 4. Validate cache integrity
  try {
    const cache = JSON.parse(fs.readFileSync(cacheFile));
    if (cache.metadata.commit_hash !== mainCommit) {
      console.log("⚠️ Cache commit mismatch");
      return null;
    }

    console.log("✅ Using cached analysis (age: " + formatDuration(cacheAge) + ")");
    return cache;
  } catch (e) {
    console.log("💔 Cache corrupted, will regenerate");
    return null;
  }
}
```

#### Cache Benefits

- **Speed**: 80-90% faster on subsequent runs (skip main branch analysis)
- **Consistency**: Same baseline for iterative development
- **Cost Savings**: Reduces API calls by ~50% on re-runs
- **Accuracy**: Automatically invalidates on main branch changes

### Cache Management Commands

```bash
# Force fresh analysis (ignore cache)
/project:evaluate-current-branch --force-refresh

# Use specific cache file
/project:evaluate-current-branch --cache-file /data/branch-evaluations/main-branch-cache/main-2025-08-22-14-30-abc123f.json

# Clear all caches
/project:evaluate-current-branch --clear-cache

# Show cache status
/project:evaluate-current-branch --cache-info
```

## 🎯 Comprehensive Analysis Mode

### What is Comprehensive Mode?

The `--comprehensive` flag activates the **ULTIMATE ANALYSIS MODE** - a complete, deep evaluation designed for:

- **Major releases** heading to production
- **Quarterly reviews** for board reporting
- **Critical decision points** requiring maximum confidence
- **Compliance audits** requiring full documentation
- **Investment decisions** needing complete financial modeling

### Command Usage

```bash
# Run comprehensive analysis (all features enabled)
/project:evaluate-current-branch --comprehensive

# Comprehensive with custom business context
/project:evaluate-current-branch --comprehensive --business-context .claude/q4-business-metrics.yaml

# Comprehensive with specific output directory
/project:evaluate-current-branch --comprehensive --output-dir ./board-review-q4/
```

### What Comprehensive Mode Includes

When you use `--comprehensive`, the system automatically enables:

#### 1. **Maximum Agent Deployment**

```yaml
agents_deployed:
  orchestrator: 1 x Opus 4.1 (extended thinking, 4+ hours if needed)
  metrics_collection: 5 x Haiku 3.5 (parallel data gathering)
  quality_analysis: 3 x Sonnet 4 (deep code understanding)
  complex_analysis: 4 x Opus 4.1 (risk, merge, security, business)
  cto_strategic: 1 x Opus 4.1 (executive synthesis)
  specialized: 8 x Mixed (compliance, customer, infra, productivity)
  total_agents: 22 (maximum parallelization)
```

#### 2. **All Focus Areas Activated**

- ✅ **Security Analysis**: Full CVE scanning, OWASP Top 10, pen test simulation
- ✅ **Performance Analysis**: Latency profiling, load testing projections, optimization opportunities
- ✅ **Compliance Validation**: SOC2, GDPR, HIPAA, PCI-DSS, ISO 27001, CCPA
- ✅ **Financial Modeling**: Complete TCO, ROI, NPV, IRR, break-even analysis
- ✅ **Customer Impact**: All segments analyzed, migration paths, support projections
- ✅ **Infrastructure**: Cloud cost modeling, scaling analysis, vendor risk
- ✅ **Developer Productivity**: Full DORA/SPACE metrics, individual recognition
- ✅ **Technical Debt**: Complete inventory with interest calculations

#### 3. **Extended Analysis Depth**

```yaml
analysis_settings:
  reasoning_mode: extended # All agents use maximum thinking time
  context_window: 1M # Full context for Sonnet/Opus
  max_thinking_steps: 50000 # Opus can think for hours if needed
  tool_use_enabled: true # Web search, documentation lookup
  cross_reference: true # Agents validate each other's findings
```

#### 4. **Complete Compliance Standards**

```yaml
compliance_checks:
  soc2:
    - access_controls
    - change_management
    - data_protection
    - incident_response
    - risk_assessment

  gdpr:
    - data_minimization
    - purpose_limitation
    - consent_management
    - right_to_erasure
    - data_portability

  hipaa:
    - phi_protection
    - access_logging
    - encryption_standards
    - breach_notification
    - minimum_necessary

  pci_dss:
    - network_segmentation
    - card_data_protection
    - vulnerability_management
    - access_control
    - regular_monitoring

  iso_27001:
    - information_security_policy
    - risk_management
    - asset_management
    - human_resource_security
    - physical_security
```

#### 5. **All Stakeholder Reports Generated**

```yaml
reports_generated:
  board_executive:
    pages: 2-3
    focus: strategic_impact, roi, risk
    format: executive_brief

  engineering_detailed:
    pages: 20-40
    focus: technical_details, architecture, debt
    format: comprehensive_technical

  customer_communication:
    pages: 1-2
    focus: benefits, changes, migration
    format: customer_friendly

  investor_update:
    pages: 3-5
    focus: metrics, efficiency, innovation
    format: quarterly_report

  compliance_audit:
    pages: 15-25
    focus: controls, evidence, remediation
    format: audit_trail

  security_assessment:
    pages: 10-15
    focus: vulnerabilities, threats, mitigations
    format: security_report
```

#### 6. **Multi-Horizon Analysis**

```yaml
time_horizons:
  immediate:
    - deployment_readiness
    - critical_bugs
    - security_vulnerabilities

  week_1:
    - customer_adoption
    - performance_metrics
    - support_volume

  month_1:
    - revenue_impact
    - churn_effects
    - operational_costs

  quarter:
    - roi_validation
    - debt_accumulation
    - velocity_changes

  year:
    - strategic_positioning
    - technical_evolution
    - market_competitiveness
```

#### 7. **Deep Merge Analysis**

```yaml
merge_analysis:
  conflict_detection:
    - textual_conflicts
    - semantic_conflicts
    - logical_inconsistencies
    - api_contract_breaks

  integration_testing:
    - required_tests: [list]
    - affected_services: [map]
    - dependency_impacts: [graph]

  deployment_strategy:
    - blue_green_feasibility
    - canary_rollout_plan
    - feature_flag_requirements
    - rollback_procedures
```

#### 8. **Financial Deep Dive**

```yaml
financial_modeling:
  immediate_costs:
    development: person_hours × rate
    infrastructure: cloud_delta
    third_party: api_costs
    opportunity: delayed_features

  revenue_projections:
    new_customers: acquisition_rate × clv
    retention: churn_reduction × arr
    upsell: feature_adoption × expansion

  investment_analysis:
    npv: 5_year_discounted_cashflow
    irr: internal_rate_of_return
    payback: months_to_positive
    sensitivity: risk_adjusted_scenarios
```

### Comprehensive Mode Output

#### File Structure

```bash
data/
└── 2025-08-23-[branch-name]-comprehensive/
    ├── executive-summary.md              # 2-3 page CEO/Board summary
    ├── detailed-report.md                # 40+ page complete analysis
    ├── reports/                          # Specialized reports
    │   ├── 01-technical-assessment.md        # Engineering detail
    │   ├── 02-security-report.md            # Security & vulnerability analysis
    │   ├── 03-compliance-audit.md           # Full compliance documentation
    │   ├── 04-financial-analysis.md         # Complete financial modeling
    │   ├── 05-customer-impact.md            # Customer segment analysis
    │   ├── 06-infrastructure-costs.md       # Cloud & vendor analysis
    │   ├── 07-developer-productivity.md     # Team performance metrics
    │   ├── 08-technical-debt-inventory.md   # Complete debt catalog
    │   ├── 09-merge-complexity.md           # Integration analysis
    │   ├── 10-risk-assessment.md            # Risk matrix & mitigations
    │   ├── 11-monitoring-plan.md            # Post-deployment monitoring
    │   └── 12-rollback-procedures.md        # Emergency procedures
    ├── stakeholder-comms/                # Ready-to-send communications
    │   ├── board-brief.md
    │   ├── investor-update.md
    │   ├── customer-notification.md
    │   └── team-announcement.md
    ├── wip/                              # ALL intermediate agent outputs (22 files)
    │   ├── 01-orchestrator-initial.json
    │   ├── 02-22-[agent-outputs].json   # All 22 agent results saved
    │   └── 23-orchestrator-final.json
    ├── raw-data/                         # Unprocessed data
    │   ├── agent-outputs.json
│   │   ├── metrics.csv
│   │   └── compliance-evidence.zip
│   └── index.html                       # Interactive dashboard
```

#### Executive Summary Example (Comprehensive Mode)

```markdown
# COMPREHENSIVE BRANCH EVALUATION

## Executive Decision Brief

**Date**: 2025-08-22 14:30 UTC
**Branch**: feat/major-platform-upgrade
**Evaluation Type**: COMPREHENSIVE (22 agents, 6-phase analysis)
**Total Analysis Time**: 12 minutes 34 seconds
**Confidence Level**: 98.5%

### 🎯 STRATEGIC VERDICT: APPROVE WITH CONDITIONS

**Decision Confidence**: VERY HIGH
**Risk-Adjusted ROI**: 4.2x over 12 months
**Payback Period**: 3.5 months

### 📁 DETAILED REPORTS LOCATION

**Full Analysis Available**: `data/2025-08-23-[branch-name]-comprehensive/`

- Executive Summary: `executive-summary.md` (2-3 pages)
- Detailed Report: `detailed-report.md` (40+ pages)
- Specialized Reports: `reports/` directory (12 focused analyses)
- Stakeholder Communications: `stakeholder-comms/` (ready-to-send)
- All Agent Outputs: `wip/` directory (22 intermediate results)
- Raw Data & Evidence: `raw-data/` directory
- Interactive Dashboard: `index.html`

### 📊 10-DIMENSIONAL ASSESSMENT MATRIX

| Dimension         | Score    | Δ from Baseline | Industry Percentile | Risk Level |
| ----------------- | -------- | --------------- | ------------------- | ---------- |
| Code Quality      | A+       | +2 grades       | 95th                | LOW        |
| Security          | A        | Maintained      | 90th                | LOW        |
| Performance       | A-       | +15%            | 88th                | LOW        |
| Scalability       | B+       | +1 grade        | 82nd                | MEDIUM     |
| Compliance        | PASS     | All standards   | 100%                | LOW        |
| Financial ROI     | 4.2x     | +$450K ARR      | 92nd                | LOW        |
| Customer Impact   | POSITIVE | +8 NPS          | 85th                | LOW        |
| Technical Debt    | -180 hrs | -$27K           | 94th                | LOW        |
| Team Productivity | +22%     | Top quartile    | 91st                | LOW        |
| Innovation Index  | 8.5/10   | +2.1            | 89th                | LOW        |

### 💰 FINANCIAL EXECUTIVE SUMMARY

- **Total Investment**: $125,000 (833 person-hours)
- **12-Month Return**: $525,000 (4.2x ROI)
- **Break-Even**: Month 3.5
- **5-Year NPV**: $1,850,000 (12% discount rate)
- **IRR**: 127%

### 🚨 CRITICAL REQUIREMENTS (Must Complete Before Merge)

1. **Security Patch**: Update dependencies for CVE-2024-XXXX (2 hours)
2. **Performance Fix**: Resolve N+1 query in UserService (4 hours)
3. **Compliance Doc**: Update GDPR data flow diagram (1 hour)

### ✅ COMPLIANCE CERTIFICATION

- **SOC2**: ✅ COMPLIANT (Type II ready)
- **GDPR**: ✅ COMPLIANT (All articles satisfied)
- **HIPAA**: ✅ COMPLIANT (PHI protection verified)
- **PCI-DSS**: ✅ COMPLIANT (Level 2 requirements met)
- **ISO 27001**: ✅ ALIGNED (93% control coverage)

### 📈 BUSINESS IMPACT PROJECTION

**Q1 Impact**:

- Customer Acquisition: +12% (45 new enterprise accounts)
- Churn Reduction: -1.2% ($180K ARR saved)
- Operational Efficiency: +15% ($75K/quarter saved)
- Market Position: Move from #4 to #3 in category

**Annual Projection**:

- Revenue Impact: +$525K ARR
- Cost Savings: $300K operational
- Market Share: +2.5 percentage points
- Customer Satisfaction: +8 NPS points

### 🏆 EXCEPTIONAL ACHIEVEMENTS

1. **Technical Debt Elimination**: Removed 180 hours of accumulated debt
2. **Test Coverage Excellence**: Increased from 67% to 94% (+27%)
3. **Performance Optimization**: 34% faster response times achieved
4. **Security Hardening**: Zero high/critical vulnerabilities
5. **Architecture Modernization**: 45% of codebase modernized

### 👥 TEAM RECOGNITION

**Outstanding Performance by Development Team**

- Delivered 187% of baseline productivity
- Zero bugs introduced (100% quality score)
- Best quarterly performance in 2 years
- Recommended for Q4 Excellence Award

### 📋 BOARD-LEVEL RECOMMENDATIONS

**IMMEDIATE ACTIONS** (This Week):

1. ✅ Approve merge with listed conditions
2. 📊 Allocate monitoring resources for Week 1
3. 🎯 Prepare customer communication plan
4. 💰 Approve performance bonuses for team

**STRATEGIC INITIATIVES** (This Quarter):

1. 🚀 Accelerate similar modernization across platform
2. 📈 Increase engineering headcount by 2 to maintain velocity
3. 🎯 Target enterprise segment with new capabilities
4. 💡 Patent innovative approaches developed

**LONG-TERM IMPLICATIONS** (12-24 Months):

1. **Competitive Advantage**: 6-month lead on nearest competitor
2. **Platform Evolution**: Foundation for AI/ML integration
3. **Acquisition Value**: +$5-10M enterprise value increase
4. **IPO Readiness**: Compliance frameworks now audit-ready

### 🔍 RISK ASSESSMENT & MITIGATION

| Risk                   | Probability   | Impact | Mitigation            | Owner   |
| ---------------------- | ------------- | ------ | --------------------- | ------- |
| Integration Issues     | LOW (15%)     | MEDIUM | Staged rollout plan   | DevOps  |
| Customer Confusion     | LOW (20%)     | LOW    | Documentation ready   | Support |
| Performance Regression | VERY LOW (5%) | HIGH   | Monitoring + rollback | SRE     |
| Competitor Response    | MEDIUM (40%)  | MEDIUM | Fast-follow features  | Product |

### 📊 DECISION CONFIDENCE FACTORS

- **Code Analysis**: 22 parallel agents, 50,000+ decision points evaluated
- **Historical Comparison**: Outperforms 94% of similar branches
- **Risk Assessment**: 98.5% confidence in success criteria
- **Financial Validation**: Conservative modeling with 20% buffer
- **Compliance Verification**: 100% automated control testing

### 🎬 RECOMMENDED DEPLOYMENT STRATEGY

**Blue-Green Deployment with Staged Rollout**

1. **Hour 0-1**: Deploy to staging, final validation
2. **Hour 2-4**: 5% canary to free tier users
3. **Hour 4-8**: 25% rollout to SMB segment
4. **Day 2**: 50% rollout including enterprise
5. **Day 3**: 100% if success criteria met

### 📈 SUCCESS METRICS (Week 1 Monitoring)

- Error Rate: Must stay < 0.1%
- Response Time P95: Must stay < 200ms
- Customer Complaints: Must stay < 5
- Revenue Impact: Must stay > -0.5%
- Rollback Trigger: Any metric exceeds threshold

### FINAL EXECUTIVE RECOMMENDATION

**This branch represents exceptional engineering work that advances our strategic objectives while maintaining operational excellence. The 4.2x ROI, combined with comprehensive risk mitigation and compliance validation, makes this a HIGH-CONFIDENCE APPROVE decision.**

**Recommended for immediate merge following completion of 3 critical items (7 hours total effort).**

---

_This comprehensive evaluation was conducted using 22 specialized AI agents analyzing 50,000+ decision points across 12 dimensions over 12 minutes._

**📁 Complete documentation package saved at: `data/2025-08-23-[branch-name]-comprehensive/`**

- Executive Summary & 40+ page Detailed Report
- 12 Specialized Reports in `reports/` directory
- 22 Agent Outputs preserved in `wip/` directory
- Ready-to-send Stakeholder Communications
- Interactive Dashboard & Raw Data Exports
- Total: 200+ pages of comprehensive analysis
```

### Time and Cost Implications

#### Comprehensive Mode Resources

```yaml
execution_metrics:
  time:
    minimum: 8 minutes
    typical: 12-15 minutes
    maximum: 30 minutes (very large branches)

  cost:
    minimum: $3.00
    typical: $8-12
    maximum: $25.00 (respects cost limit)

  agents:
    total: 22
    parallel_groups: 4
    phases: 6

  tokens:
    input: ~500K-2M
    output: ~100K-500K
    total: ~600K-2.5M
```

#### When to Use Comprehensive Mode

**RECOMMENDED FOR**:

- 🚀 **Major releases** going to production
- 📊 **Quarterly reviews** for board meetings
- 💰 **High-value features** affecting revenue
- 🔒 **Security-critical** changes
- 📋 **Compliance audits** requiring documentation
- 🏆 **Team performance** reviews
- 💼 **M&A due diligence** technical assessments
- 📈 **Investor updates** requiring metrics

**NOT NEEDED FOR**:

- 🐛 Small bug fixes
- 📝 Documentation updates
- 🎨 UI/UX tweaks
- 🧪 Experimental features
- 🔧 Configuration changes
- 📚 README updates

### Comprehensive Mode Automation

```bash
# Set up weekly comprehensive review (add to CI/CD)
if [ "$(date +%u)" -eq 5 ]; then  # Every Friday
  /project:evaluate-current-branch --comprehensive \
    --business-context .claude/current-metrics.yaml \
    --output-dir ./weekly-reviews/week-$(date +%V)/
fi

# Pre-release comprehensive check
if [[ "$BRANCH" == release/* ]]; then
  /project:evaluate-current-branch --comprehensive \
    --compliance-standards SOC2,GDPR,HIPAA,PCI \
    --stakeholder-report all \
    --output-dir ./release-audits/
fi
```

### Cache File Format

````json
{
  "metadata": {
    "branch": "main",
    "commit_hash": "abc123f",
    "timestamp": "2025-08-22T14:30:00Z",
    "evaluation_version": "2.0",
    "total_files": 1247,
    "total_lines": 87432
  },
  "analysis": {
    "metrics": { /* Agent A results */ },
    "quality": { /* Agent B results */ },
    "business": { /* Agent C results */ },
    "merge_base": { /* Merge analysis */ }
  },
  "baselines": {
    "three_month_average": {
      "commits_per_day": 12.4,
      "lines_per_commit": 147,
      "test_coverage_delta": 2.1
    }
  }
}

### Executive Summary Contents
- **Overview**: Branch name, comparison base, key metrics
- **Key Achievements**: Top 3-5 accomplishments
- **Critical Issues**: Any P0/P1 issues found
- **CTO Verdict**: Strategic assessment and recommendations
- **Developer Recognition**: Performance highlights
- **Action Items**: Prioritized next steps

### Detailed Report Contents
- **Full Agent Analysis**: Complete output from all agents
- **Raw Metrics**: All collected data points
- **Code Samples**: Specific examples of good/bad patterns
- **Detailed Recommendations**: Line-by-line suggestions
- **Performance Data**: Timing, productivity metrics
- **Technical Debt Inventory**: Complete debt assessment
- **Merge Analysis**: Full conflict report

### File Output Implementation

```bash
# The command automatically:
1. Checks for cached main branch analysis
2. Creates timestamped filenames
3. Splits report into executive/detailed sections
4. Saves to data/evaluation-reports/
5. Caches main branch analysis if needed
6. Displays summary in terminal
7. Shows file paths for reference

# Example output (first run):
🔍 Checking main branch cache...
❌ No valid cache found for main@abc123f
🚀 Analyzing main branch (this will be cached)...
⏳ Running 7 parallel agents...
💾 Caching main branch analysis for future runs
📊 Branch Evaluation Complete!
📄 Executive Summary: data/evaluation-reports/2025-08-22-14-30-executive-summary.md
📚 Detailed Report: data/evaluation-reports/2025-08-22-14-30-detailed-report.md
💾 Main Cache: data/branch-evaluations/main-branch-cache/main-2025-08-22-14-30-abc123f.json
✅ Reports saved successfully!

# Example output (subsequent run):
🔍 Checking main branch cache...
✅ Using cached analysis for main@abc123f (age: 2 hours)
🚀 Analyzing current branch only...
⏳ Running 7 parallel agents...
📊 Branch Evaluation Complete!
📄 Executive Summary: data/evaluation-reports/2025-08-22-14-31-executive-summary.md
📚 Detailed Report: data/evaluation-reports/2025-08-22-14-31-detailed-report.md
✅ Reports saved successfully! (80% faster with cache)
````

### Iterative Development Workflow

```bash
# Day 1: Initial evaluation
/project:evaluate-current-branch
# ⏱️ Full analysis: ~3-5 minutes
# 💾 Main branch cached

# Day 1: After improvements
/project:evaluate-current-branch
# ⏱️ Using cache: ~30-60 seconds
# 📈 Shows progress vs same baseline

# Day 2: Continue work
/project:evaluate-current-branch
# ⏱️ Using cache: ~30-60 seconds
# 📊 Consistent baseline for comparison

# Day 3: Main branch updated
git pull origin main
/project:evaluate-current-branch
# 🔄 Cache invalidated (new commits detected)
# ⏱️ Full analysis: ~3-5 minutes
# 💾 New cache created

# Force refresh if needed
/project:evaluate-current-branch --force-refresh
# 🔄 Ignores cache, runs full analysis
```

### Manual Save Options

```bash
# Save to custom location
/project:evaluate-current-branch --output-dir ./my-reports/

# Custom filename prefix
/project:evaluate-current-branch --report-prefix "sprint-23-review"

# Skip file saving (terminal only)
/project:evaluate-current-branch --no-save
```

### Report Format Examples

#### Executive Summary Format (2-3 pages)

```markdown
# Branch Evaluation: Executive Summary

Date: 2025-08-22 14:30 UTC
Branch: feat/typescript-score-and-draft-migration
Base: main

## 🎯 Key Metrics

- Files Changed: 127
- Lines Added: +8,432 / Removed: -3,211
- Test Coverage: 87.3% (+5.2%)
- Technical Debt: -47 hours (improvement)
- Merge Difficulty: LOW (2 minor conflicts)

## ✨ Major Achievements

1. **TypeScript Migration**: Successfully migrated 45 JavaScript files
2. **Performance Gain**: 34% faster execution on scoring pipeline
3. **Test Coverage**: Added 127 new tests, improved coverage by 5.2%

## 🚨 Critical Issues

- None identified

## 💼 CTO Assessment

**Verdict**: APPROVE WITH COMMENDATION

- Exceptional code quality improvement
- Strategic technical debt reduction
- Ready for immediate merge

## 👏 Developer Recognition

- **Productivity**: 187% of 3-month average
- **Quality**: Top 5% percentile
- **Achievement**: "TypeScript Champion" milestone unlocked

## 📋 Recommended Actions

1. ✅ Merge immediately (low risk)
2. 📚 Document new TypeScript patterns
3. 🎯 Apply similar migration to remaining JS files
```

#### Detailed Report Structure (10-20 pages)

```markdown
# Branch Evaluation: Detailed Report

[Full timestamp and metadata]

## Table of Contents

1. Pre-Analysis Results
2. Agent Group A: Core Metrics
3. Agent Group B: Quality Analysis
4. Agent Group C: Business Impact
5. Merge Complexity Analysis
6. CTO Strategic Assessment
7. Developer Productivity Report
8. Appendices

[... 10-20 pages of detailed analysis ...]
```

## Notes

### Performance & Cost

- **10-agent parallel system** provides 8-10x speedup over sequential processing
- **Cost range**: $0.50-5.00 (standard), $8-12 (comprehensive mode)
- **Main branch caching** reduces subsequent evaluation time by 80-90%
- **Typical timing**:
  - Standard: First run ~3-5 minutes, cached runs ~30-60 seconds
  - Comprehensive: 12-15 minutes with 22 agents and full analysis

### 🎯 Comprehensive Mode (NEW)

- **Ultimate Analysis**: `--comprehensive` flag enables all 22 agents with extended reasoning
- **Complete Coverage**: All focus areas, compliance standards, and stakeholder reports
- **Deep Financial Modeling**: TCO, ROI, NPV, IRR with 5-year projections
- **Full Compliance Suite**: SOC2, GDPR, HIPAA, PCI-DSS, ISO 27001, CCPA validation
- **Multi-Horizon Analysis**: Immediate, Week 1, Month 1, Quarter, and Year projections
- **200+ Page Documentation**: Complete audit trail with evidence and appendices
- **When to Use**: Major releases, quarterly reviews, board meetings, compliance audits
- **Investment**: 12-15 minutes, $8-12 cost, 98.5% confidence level

### Key Features (10/10 CTO-Level)

- **Business Context Integration**: Loads financial metrics, OKRs, and constraints
- **Security & Compliance**: CVE scanning, OWASP validation, full compliance checks
- **Financial Analysis**: ROI, NPV, payback period, cost-benefit modeling
- **Customer Impact**: Breaking change detection, migration planning, NPS prediction
- **Infrastructure Cost**: Cloud resource projections, vendor risk assessment
- **Executive Decision Framework**: Go/no-go criteria with confidence levels
- **Operational Readiness**: Deployment planning, monitoring, rollback strategies
- **Post-Deployment Monitoring**: Automated success criteria and rollback triggers
- **Stakeholder Templates**: Board, engineering, customer, investor communications
- **Risk Management**: Probability × impact matrix with mitigation ownership

### Technical Requirements

- Requires `cloc` for code metrics: `brew install cloc`
- Optional security tools: `trivy`, `semgrep` for enhanced scanning
- Git configured with origin remote
- Sufficient API rate limits for parallel execution
- Business context file (`data/business-context.yaml`) for financial analysis

### Data Management

- Reports saved to `data/evaluation-reports/` (gitignored)
- Main branch cache in `data/branch-evaluations/` with commit validation
- Cache valid for 7 days or until new commits detected
- Business metrics loaded from configurable YAML/JSON file
- Comprehensive mode creates structured subdirectory with 13+ report files

### Execution Strategies

- **Focus areas**: security, performance, compliance, financial, or all
- **Model strategies**: auto, cost-optimized, performance-optimized
- **Risk tolerance**: low, medium, high thresholds
- **Stakeholder reports**: board, engineering, customer, investor formats
- **Comprehensive mode**: All strategies at maximum depth

### Success Metrics

- Provides CTO-level strategic assessment with 95-98.5% confidence
- Reduces decision time from hours to minutes
- Quantifies technical debt in dollars and person-hours
- Predicts customer impact and revenue implications
- Ensures compliance and security standards
- Enables data-driven go/no-go decisions
- Comprehensive mode: 10-dimensional assessment matrix with industry percentiles
