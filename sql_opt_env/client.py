# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

"""Sql Opt Env Environment Client."""

from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import SqlOptAction, SqlOptObservation


class SqlOptEnv(EnvClient[SqlOptAction, SqlOptObservation, State]):
    def _step_payload(self, action: SqlOptAction) -> Dict:
        return {
            "rewritten_sql": action.rewritten_sql,
        }

    def _parse_result(self, payload: Dict) -> StepResult[SqlOptObservation]:
        obs_data = payload.get("observation", {})
        observation = SqlOptObservation(
            original_sql=obs_data.get("original_sql", ""),
            schema_ddl=obs_data.get("schema_ddl", ""),
            current_latency_ms=obs_data.get("current_latency_ms", 0.0),
            explain_plan=obs_data.get("explain_plan", ""),
            episode_step=obs_data.get("episode_step", 0),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
