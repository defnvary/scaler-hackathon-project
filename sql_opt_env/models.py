# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class SqlOptAction(Action):
    """Action for the Sql Opt Env environment - the optimized query."""

    rewritten_sql: str = Field(..., description="Agent's output - the optimized query")


class SqlOptObservation(Observation):
    """Observation from the Sql Opt Env environment."""

    original_sql: str = Field(default="", description="The slow query to optimize")
    schema_ddl: str = Field(
        default="", description="CREATE TABLE statements for context"
    )
    current_latency_ms: float = Field(
        default=0.0, description="Baseline execution time"
    )
    explain_plan: str = Field(
        default="", description="EXPLAIN ANALYZE JSON of original query"
    )
    episode_step: int = Field(default=0, description="Current step in the episode")
    task_name: str = Field(
        default="", description="Name of the current optimization task"
    )
    difficulty: str = Field(default="", description="Difficulty level of the task")
