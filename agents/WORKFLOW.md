# Human-in-the-Loop Workflow

## Complete Flow: From Discovery to Approval

### Step 1: Generate Data Product Ideas

Run the full agent pipeline (monitoring + learning):

```bash
cd agents
source venv/bin/activate
python bootstrap.py --dry-run
```

**Output:**
```
✨ Generated 4 data product ideas!

📋 Generated Data Product Ideas:
  1. Gaming Analytics Hub (gaming)
  2. Real-time Customer Journey Tracker (e-commerce)
  3. Smart Fleet Insights (fleet_management)
  4. Pizza Delivery Intelligence (food_delivery)

📍 Next Steps:
  - Review ideas with human refinement:
    python human_refinement.py --dry-run
```

### Step 2: Review and Approve Ideas (Interactive)

Launch the human refinement interface:

```bash
python human_refinement.py --dry-run
```

**What You'll See:**

```
================================================================================
IDEA #1: Smart Fleet Insights
================================================================================

📌 Domain: fleet_management
🔖 Status: RAW
🎯 Complexity: MEDIUM
📊 Confidence: 0.85

📝 Description:
   Comprehensive fleet management solution combining real-time location data,
   sensor information, and vehicle descriptions for optimized fleet operations.

💡 Reasoning:
   Active consumption patterns across fleet-related topics suggest strong
   operational use. Combining these streams enables real-time fleet
   optimization and predictive maintenance.

📦 Related Topics (3):
   - location
   - sensors
   - description

👥 Potential Users:
   - Fleet Managers
   - Logistics Planners
   - Maintenance Teams
   - Operations Analysts

────────────────────────────────────────────────────────────────────────────────
Actions:
  [a] Approve - Move to evaluation
  [r] Reject - Mark as rejected
  [e] Edit - Modify idea details
  [s] Skip - Review later
  [q] Quit - Exit refinement
────────────────────────────────────────────────────────────────────────────────

Your choice:
```

### Action Examples

#### Approve an Idea
```
Your choice: a

✅ Idea APPROVED - will proceed to evaluation
   ✅ Updated in Kafka (or saved to file in dry-run)
```

The idea status changes: `RAW` → `APPROVED`

#### Reject an Idea
```
Your choice: r

Rejection reason (optional): Too complex for initial rollout

❌ Idea REJECTED
   ✅ Updated in Kafka
```

The idea status changes: `RAW` → `REJECTED`

#### Edit an Idea
```
Your choice: e

✏️  Edit Idea (press Enter to keep current value)

Title [Smart Fleet Insights]: Fleet Operations Hub

Description [Comprehensive fleet...]: Real-time fleet monitoring and analytics

Domain [fleet_management]:

Complexity [MEDIUM]
  Options: LOW, MEDIUM, HIGH, VERY_HIGH
  Choice: LOW

Related Topics (current: 3)
  location, sensors, description...
  Add/replace (comma-separated): fleet_mgmt_location, fleet_mgmt_sensors, fleet_mgmt_description

✅ Idea updated!

Approve this idea now? [y/N]: y

✅ Idea APPROVED after refinement
```

The idea is updated with your changes and marked as `REFINED` or `APPROVED`

#### Skip for Later
```
Your choice: s

⏭️  Skipped - will remain in RAW status
```

Moves to next idea without changing status

#### Quit Early
```
Your choice: q

👋 Exiting refinement...

================================================================================
REFINEMENT SUMMARY
================================================================================
✅ Approved: 2
❌ Rejected: 1
✏️  Modified: 0
📝 Remaining: 1
```

### Step 3: View Approval Summary

At the end of review, you'll see:

```
================================================================================
REFINEMENT SUMMARY
================================================================================
✅ Approved: 3
❌ Rejected: 1
✏️  Modified: 1
📝 Remaining: 0

🎯 Approved Ideas:
   - Gaming Analytics Hub (gaming)
   - Smart Fleet Insights (fleet_management)
   - Pizza Delivery Intelligence (food_delivery)
```

### What Happens to Approved Ideas?

**In Dry-Run Mode:**
- Updated idea files saved to `dry-run-output/raw-idea-*.json`
- Status field updated to `APPROVED`

**In Production Mode:**
- Ideas published back to `agent-state-raw-ideas` Kafka topic
- Compacted topic keeps only latest version per idea_id
- Approved ideas ready for next phase: **Evaluation Agents**

## Next Phase: Evaluation (Coming Soon)

Approved ideas will flow to evaluation agents:

1. **Scope Agent** - Assess complexity and feasibility
   - Reviews topics, schemas, dependencies
   - Identifies potential challenges
   - Estimates scope creep risk

2. **Time Agent** - Estimate timeline
   - Development time estimate
   - Testing requirements
   - Deployment timeline

3. **Cost Agent** - Calculate resource requirements
   - Infrastructure costs
   - Engineering effort
   - Ongoing maintenance

4. **Decision Prompt Agent** - Synthesize recommendations
   - Consolidates all evaluations
   - Provides trade-off analysis
   - Final human checkpoint: Go/No-Go

## Example Complete Session

```bash
# Generate ideas
$ python bootstrap.py --dry-run
✨ Generated 4 data product ideas!

# Review ideas
$ python human_refinement.py --dry-run

[Review Idea 1: Gaming Analytics Hub]
Your choice: a
✅ Idea APPROVED

[Review Idea 2: Customer Journey Tracker]
Your choice: e
# Edit complexity from VERY_HIGH to HIGH, approve
✅ Idea APPROVED after refinement

[Review Idea 3: Smart Fleet Insights]
Your choice: a
✅ Idea APPROVED

[Review Idea 4: Pizza Delivery Intelligence]
Your choice: r
Rejection reason: Low priority for Q1
❌ Idea REJECTED

================================================================================
REFINEMENT SUMMARY
================================================================================
✅ Approved: 3
❌ Rejected: 1

🎯 Approved Ideas:
   - Gaming Analytics Hub (gaming)
   - Real-time Customer Journey Tracker (e-commerce)
   - Smart Fleet Insights (fleet_management)
```

## Key Design Principles

1. **Human Strategic Oversight**: AI proposes, humans decide
2. **Interactive, Not Automatic**: Requires explicit approval
3. **Flexible Decision Making**: Approve, reject, or refine
4. **Audit Trail**: All decisions tracked with status changes
5. **Iterative Refinement**: Can edit before approving

## Files Updated During Refinement

```
dry-run-output/
├── raw-idea-926bba51-...json  # Status: RAW → APPROVED
├── raw-idea-d7464b30-...json  # Status: RAW → REFINED → APPROVED
├── raw-idea-8be87994-...json  # Status: RAW → APPROVED
└── raw-idea-2866ebac-...json  # Status: RAW → REJECTED
```

Each file contains the complete idea with updated status and any edits made during refinement.
