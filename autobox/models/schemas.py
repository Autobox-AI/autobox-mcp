"""Pydantic models for Autobox MCP server."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for a simulation agent."""

    name: str
    role: str
    backstory: Optional[str] = ""
    llm_model: str = "gpt-4o-mini"


class SimulationConfig(BaseModel):
    """Configuration for a simulation."""

    name: str
    description: str
    max_steps: int = Field(default=100, ge=1)
    timeout_seconds: int = Field(default=300, ge=30)
    agents: List[Dict[str, Any]] = Field(default_factory=list)


class SimulationStatus(BaseModel):
    """Status of a simulation."""

    id: str
    name: str
    status: str
    config_path: Optional[str] = None
    container_id: Optional[str] = None
    progress: Optional[int] = None
    summary: Optional[str] = None


class SimulationMetrics(BaseModel):
    """Metrics for a simulation."""

    simulation_id: str
    step_count: int = 0
    agent_interactions: int = 0
    completion_time: Optional[float] = None
    success: Optional[bool] = None