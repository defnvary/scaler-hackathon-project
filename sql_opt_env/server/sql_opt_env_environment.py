import json
from uuid import uuid4
import sqlglot

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State, EnvironmentMetadata
from pydantic import Field

try:
    from ..models import SqlOptAction, SqlOptObservation
except (ImportError, ModuleNotFoundError):
    from models import SqlOptAction, SqlOptObservation

from sql_opt_env.db import setup_db, execute_query_metrics
from sql_opt_env.query_bank import query_bank


class SqlOptEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.max_steps = 1
        setup_db()
        self.current_original_sql = ""
        self.current_schema_ddl = ""
        self.current_task_name = ""
        self.current_difficulty = ""
        self.baseline_ms = 0.0
        self.baseline_hash = ""
        self.baseline_plan = "{}"

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="sql_opt_env",
            description="SQL Query Optimizer environment for RL training",
            version="1.0.0",
            author="Antigravity",
        )

    def reset(self) -> SqlOptObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)

        # Sample a slow query, tracking difficulty
        sql, schema, difficulty = query_bank.sample()
        self.current_original_sql = sql
        self.current_schema_ddl = schema
        self.current_difficulty = difficulty

        # Determine task name from query bank
        self.current_task_name = "optimize_sql"
        for diff in query_bank.queries:
            for task in query_bank.queries[diff]:
                if task["sql"].strip() == sql.strip():
                    self.current_task_name = task.get("name", "optimize_sql")

        # Get baseline metrics
        ms, plan, res_hash, err = execute_query_metrics(sql)
        self.baseline_ms = ms
        self.baseline_hash = res_hash
        self.baseline_plan = json.dumps(plan) if plan else "{}"

        return SqlOptObservation(
            original_sql=self.current_original_sql,
            schema_ddl=self.current_schema_ddl,
            current_latency_ms=self.baseline_ms,
            explain_plan=self.baseline_plan,
            episode_step=0,
            done=False,
            reward=0.0,
            task_name=self.current_task_name,
            difficulty=self.current_difficulty,
        )

    def step(self, action: SqlOptAction) -> SqlOptObservation:
        self._state.step_count += 1
        done = self._state.step_count >= self.max_steps
        rewritten_sql = action.rewritten_sql

        # strictly 0.0 to 1.0 scale
        reward = 0.0
        new_ms = 0.0
        new_plan = "{}"

        # 1. Syntax validity (0.2 max)
        try:
            sqlglot.parse_one(rewritten_sql, read="postgres")
            reward += 0.2
        except Exception as e:
            return self._build_obs(
                0.0, '{"error": "syntax_error"}', done=True, reward=0.0
            )

        # Execute rewritten query
        ms, plan, res_hash, err = execute_query_metrics(rewritten_sql)
        new_ms = ms
        new_plan = json.dumps(plan) if plan else "{}"

        if err:
            return self._build_obs(
                0.0, json.dumps({"error": str(err)}), done=True, reward=reward
            )

        # 2. Execution success (0.2 max)
        reward += 0.2

        # 3. Semantic correctness (0.3 max)
        if res_hash == self.baseline_hash:
            reward += 0.3

            # 4. Latency reduction (0.3 max)
            if self.baseline_ms > 0:
                reduction = (self.baseline_ms - new_ms) / self.baseline_ms
                if reduction > 0:
                    reward += min(0.3, reduction * 0.5)  # Scale up to 0.3

        return self._build_obs(new_ms, new_plan, done, round(reward, 2))

    def _build_obs(self, ms, plan, done, reward):
        return SqlOptObservation(
            original_sql=self.current_original_sql,
            schema_ddl=self.current_schema_ddl,
            current_latency_ms=ms,
            explain_plan=plan,
            episode_step=self._state.step_count,
            done=done,
            reward=reward,
            task_name=self.current_task_name,
            difficulty=self.current_difficulty,
        )

    @property
    def state(self) -> State:
        return self._state
