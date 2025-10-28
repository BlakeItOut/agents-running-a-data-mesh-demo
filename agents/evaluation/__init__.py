"""
Evaluation Layer - The Iron Triangle (Shark Tank Agents)

This layer contains three adversarial agents that challenge approved data product ideas:
- Scope Agent: Complexity and execution risk assessment
- Time Agent: Timeline and schedule risk analysis
- Cost Agent: Resource and budget analysis

Plus the Decision Agent that synthesizes all three perspectives.

These agents act like tough Shark Tank investors who ask hard questions
and push back on unrealistic assumptions.
"""

from .scope import run_scope_agent
from .time import run_time_agent
from .cost import run_cost_agent
from .decision import run_decision_agent

__all__ = [
    'run_scope_agent',
    'run_time_agent',
    'run_cost_agent',
    'run_decision_agent'
]
