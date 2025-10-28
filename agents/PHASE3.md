# Phase 3: Evaluation Layer - The Iron Triangle (Shark Tank)

Phase 3 implements the **Evaluation Layer** where three adversarial "Shark Tank" agents challenge approved data product ideas across the iron triangle of project management: **Scope**, **Time**, and **Cost**.

## Overview

After the Learning Agent generates ideas and humans approve them (Phase 2), the approved ideas must pass through rigorous evaluation before moving to solution design. Three specialized agents act like tough Shark Tank investors, each focused on a critical dimension:

1. **Scope Agent** - Complexity & execution risk (like an investor who's seen too many projects fail due to scope creep)
2. **Time Agent** - Timeline & schedule risk (like an investor who knows everything takes 2-3x longer than estimated)
3. **Cost Agent** - Budget & ROI analysis (like Kevin O'Leary - all about the money)

Then a **Decision Agent** synthesizes all three perspectives into a final recommendation for human approval.

## Architecture Flow

```
Approved Ideas (from Phase 2)
         ↓
    ┌────────────────────────┐
    │   Scope Agent          │ → scope-challenges
    │   (Complexity Risk)    │
    └────────────────────────┘
         ↓
    ┌────────────────────────┐
    │   Time Agent           │ → time-challenges
    │   (Schedule Risk)      │
    └────────────────────────┘
         ↓
    ┌────────────────────────┐
    │   Cost Agent           │ → cost-challenges
    │   (Budget & ROI)       │
    └────────────────────────┘
         ↓
    ┌────────────────────────┐
    │   Decision Agent       │ → decisions
    │   (Synthesize)         │
    └────────────────────────┘
         ↓
    Human Approval
         ↓
    Approved Decisions → Solution Design (Phase 4)
```

## The Iron Triangle Agents

### 1. Scope Agent (`agents/evaluation/scope.py`)

**Personality**: Skeptical complexity watchdog

The Scope Agent challenges assumptions about how "simple" an idea really is. It:
- Evaluates **true complexity** (not initial estimates)
- Identifies **integration points** that could fail
- Assesses **scope creep risk**
- Lists **technical challenges** in detail
- Identifies **dependencies** that must be in place first
- Recommends **scope adjustments** to make the project manageable

**Output**: ScopeChallenge
- `complexity_rating`: TRIVIAL, SIMPLE, MODERATE, COMPLEX, VERY_COMPLEX
- `scope_creep_risk`: MINIMAL, LOW, MODERATE, HIGH, CRITICAL
- `technical_challenges`: List of specific challenges
- `integration_points`: Systems/services that need integration
- `dependencies`: Prerequisites required
- `recommended_scope_adjustments`: Ways to reduce scope

**Shark Tank Personality**:
> "I've seen too many projects fail due to scope creep. If it's complex, I'll say it. Don't sugarcoat. Better to know now than after 6 months of wasted effort."

### 2. Time Agent (`agents/evaluation/time.py`)

**Personality**: Realistic timeline enforcer

The Time Agent knows that EVERY estimate is optimistic. It:
- Provides **realistic timeline estimates** (best/expected/worst case)
- Breaks work into **implementation phases**
- Identifies **schedule risk factors**
- Accounts for **real-world delays** (testing, reviews, rework, context switching)
- Finds **parallel work opportunities**

**Output**: TimeChallenge
- `estimated_duration_weeks`: Realistic estimate
- `best_case_weeks`: Optimistic scenario
- `worst_case_weeks`: If things go wrong
- `schedule_risk`: MINIMAL, LOW, MODERATE, HIGH, CRITICAL
- `implementation_phases`: Breakdown of work phases
- `time_risk_factors`: Things that will cause delays
- `parallel_work_opportunities`: Ways to speed up

**Shark Tank Personality**:
> "Things ALWAYS take longer than expected. I multiply estimates by 2-3x. 'You're dead to me if you miss this deadline' - better to set realistic expectations upfront."

### 3. Cost Agent (`agents/evaluation/cost.py`)

**Personality**: ROI-obsessed money manager (Kevin O'Leary)

The Cost Agent cares about **money and ROI, period**. It:
- Estimates **development costs** (low/medium/high range)
- Calculates **ongoing operational costs** (monthly infrastructure)
- Defines **resource requirements** (people, skills, duration)
- Breaks down **infrastructure costs**
- Assesses **cost risk** and **ROI potential**
- Questions the value: "How exactly does this make us money?"

**Output**: CostChallenge
- `development_cost_estimate`: {low, medium, high} in USD
- `monthly_operational_cost`: Ongoing costs
- `resource_requirements`: People needed (type, count, duration)
- `infrastructure_costs`: Breakdown by component
- `cost_risk`: MINIMAL, LOW, MODERATE, HIGH, CRITICAL
- `roi_potential`: MINIMAL, LOW, MODERATE, HIGH, VERY_HIGH
- `cost_optimization_opportunities`: Ways to reduce costs

**Shark Tank Personality**:
> "Every dollar needs to generate value. I'm ruthless about costs. 'Nice to have' is code for 'waste of money'. I'm out if the numbers don't make sense."

### 4. Decision Agent (`agents/evaluation/decision.py`)

**Personality**: Panel moderator reaching consensus

The Decision Agent acts like the Shark Tank panel after all sharks have weighed in. It:
- Synthesizes **all three challenges** into a cohesive recommendation
- Makes a **clear decision**: STRONGLY_APPROVE, APPROVE, APPROVE_WITH_CONDITIONS, RECONSIDER, or REJECT
- Provides **key findings** that combine perspectives
- Lists **conditions** if approval is conditional
- Suggests **alternative approaches**

**Output**: Decision
- `recommendation`: STRONGLY_APPROVE, APPROVE, APPROVE_WITH_CONDITIONS, RECONSIDER, REJECT
- `overall_risk`: MINIMAL, LOW, MODERATE, HIGH, CRITICAL
- `key_findings`: 3-5 most important insights
- `conditions`: What must change if approved
- `alternative_approaches`: Other ways to achieve the goal
- `summary`: Executive summary
- `detailed_reasoning`: Full synthesis

## Usage

### Quick Start (Dry-Run Mode)

```bash
cd agents

# Run full pipeline with Phase 3
python bootstrap.py --dry-run --interactive

# OR skip earlier phases if you already have approved ideas
python bootstrap.py --dry-run --interactive --skip-learning

# Run non-interactively (auto-generate, no human input)
python bootstrap.py --dry-run --skip-evaluation  # Stop before evaluation
```

### Step-by-Step Demo Mode

```bash
# Pause after each step - perfect for demoing
python bootstrap.py --dry-run --interactive --pause
```

This will:
1. Run monitoring agents (deployment, usage, metrics)
2. Synthesize current state
3. Generate data product ideas
4. Launch human refinement (approve/reject ideas)
5. **Run Scope Agent** (analyze complexity)
6. **Run Time Agent** (estimate timeline)
7. **Run Cost Agent** (calculate costs)
8. **Run Decision Agent** (synthesize recommendation)
9. Launch human approval (final go/no-go)

### Run Individual Agents

```bash
# Run evaluation agents individually
python evaluation/scope.py --dry-run
python evaluation/time.py --dry-run
python evaluation/cost.py --dry-run
python evaluation/decision.py --dry-run

# Review decisions
python human_approval.py --dry-run
```

## Output Files (Dry-Run Mode)

All evaluation outputs are saved to `agents/dry-run-output/`:

```
dry-run-output/
├── raw-idea-<uuid>.json           # Approved ideas from Phase 2
├── scope-challenge-<uuid>.json    # Scope analysis
├── time-challenge-<uuid>.json     # Timeline analysis
├── cost-challenge-<uuid>.json     # Cost analysis
└── decision-<uuid>.json           # Final decision
```

## Kafka Topics (Full Mode)

When running with real Kafka infrastructure:

- `agent-state-scope-challenges` - Scope Agent outputs
- `agent-state-time-challenges` - Time Agent outputs
- `agent-state-cost-challenges` - Cost Agent outputs
- `agent-state-decisions` - Decision Agent outputs

All topics use:
- **Log compaction** (retain latest per key)
- **Snappy compression**
- **Avro schemas** from `agents/schemas/`

## Terraform Infrastructure

Phase 3 adds 4 new Kafka topics and schemas:

```bash
cd terraform
terraform apply

# This creates:
# - 4 Kafka topics (scope/time/cost challenges, decisions)
# - 4 Avro schemas registered in Schema Registry
# - Proper RBAC permissions
```

Updated in:
- `terraform/agent-topics.tf` - Topic definitions
- `terraform/agent-schemas.tf` - Schema registrations

## Human Approval Interface

The `human_approval.py` script provides an interactive CLI for reviewing decisions:

**Actions**:
- `[a]` Approve - Proceed to solution design (Phase 4)
- `[r]` Reject - Send back to ideation
- `[d]` Defer - Review later
- `[s]` Skip - Move to next decision
- `[q]` Quit - Exit approval

**Example**:
```
================================================================================
DECISION #1: Smart Fleet Insights
================================================================================

📋 RECOMMENDATION: APPROVE_WITH_CONDITIONS
⚠️  OVERALL RISK: MODERATE
🎯 CONFIDENCE: 85%

📝 Summary:
   Strong data product with clear value, but scope needs tightening...

💡 Key Findings (3):
   • Complex real-time aggregation requires careful architecture
   • 8-12 week timeline is realistic with experienced team
   • ROI justifies investment if delivered on schedule

⚙️  Conditions (2):
   • Start with read-only API, add write capabilities in phase 2
   • Implement for single fleet segment first, expand later

Your choice: a
```

## Example: Idea Through Evaluation

Let's trace an idea through all three agents:

### Input: "Smart Fleet Insights"
- **Description**: Real-time fleet management combining location, sensors, vehicle descriptions
- **Complexity (initial)**: MEDIUM
- **Confidence**: 0.85

### Scope Agent Output:
- **Complexity (actual)**: COMPLEX
- **Scope Creep Risk**: MODERATE
- **Technical Challenges**:
  - Real-time stream aggregation at scale
  - Geo-spatial indexing for location data
  - Schema evolution for sensor types
- **Recommended Adjustments**:
  - Start with 3 data streams, add more incrementally
  - Use pre-built ksqlDB windowing, avoid custom state stores

### Time Agent Output:
- **Timeline**: 8-12 weeks (best: 6, worst: 16)
- **Schedule Risk**: MODERATE
- **Phases**:
  1. ksqlDB setup & schema design (2 weeks)
  2. Stream aggregation logic (3 weeks)
  3. API development (2 weeks)
  4. Testing & deployment (1 week)
- **Risk Factors**:
  - Geo-spatial query performance tuning
  - Schema Registry migration complexity

### Cost Agent Output:
- **Development**: $35K-$55K
- **Monthly Operations**: $450/month
- **Resources**: 1 Data Engineer (8 weeks), 0.5 Backend Dev (4 weeks)
- **ROI**: HIGH (enables $200K/year in fleet optimization)

### Decision:
- **Recommendation**: APPROVE_WITH_CONDITIONS
- **Conditions**:
  - Implement MVP with 3 streams first
  - Get performance baseline before adding features
- **Overall Risk**: MODERATE

## Configuration

The Shark Tank personalities are configured in each agent's `system_prompt`:

```python
# agents/evaluation/scope.py
system_prompt = """You are the Scope Agent - think of yourself as a tough
Shark Tank investor focused on COMPLEXITY and EXECUTION RISK.

Be SKEPTICAL and challenge assumptions..."""
```

Modify these prompts to adjust agent behavior (more/less aggressive, different focus areas, etc.).

## Next Steps

After human approval:
- **Phase 4**: Solution Agent designs implementation
- **Phase 5**: Implementation Agent creates PRs
- Deployment creates feedback loop to monitoring agents

## Troubleshooting

### No approved ideas to evaluate
```
⚠️  No approved ideas found to evaluate
```
**Solution**: Run Phase 2 first or manually create approved idea files:
```bash
python bootstrap.py --dry-run --interactive
# Approve at least one idea
```

### Claude API failures
Check your API key and backend configuration:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# OR
export CLAUDE_BACKEND=bedrock
export BEDROCK_API_KEY="..."
```

### JSON parsing errors
If an agent fails to parse Claude's response, it will fall back to conservative defaults and flag the challenge for manual review.

## Cost Considerations

**Dry-Run Mode**: ~$0.15-0.30 per full Phase 3 run (3 evaluation agents + decision)

**Full Mode with Kafka**:
- Agent topics: Minimal cost (compacted, low throughput)
- Claude API: ~$0.15-0.30 per evaluation cycle
- Total: < $1 per complete evaluation

## Development

To add new evaluation criteria:

1. Create new agent in `agents/evaluation/`
2. Define Avro schema in `agents/schemas/`
3. Add Kafka topic in `terraform/agent-topics.tf`
4. Register schema in `terraform/agent-schemas.tf`
5. Import in `bootstrap.py` and add to orchestration
6. Update Decision Agent to consider new dimension

## References

- Architecture: `/docs/architecture/agent-flow.md`
- Phase 2 (Learning): `agents/WORKFLOW.md`
- Terraform: `terraform/agent-topics.tf`, `terraform/agent-schemas.tf`
- Schemas: `agents/schemas/scope-challenge.avsc`, etc.
