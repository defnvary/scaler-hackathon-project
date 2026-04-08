# SQL Query Optimizer OpenEnv

An RL environment built for the Meta × PyTorch OpenEnv Hackathon 2026. 
The agent's task is to receive a slow SQL query and schema, and rewrite it into an optimized version.

## 🏆 Prerequisites Fulfilled
- **Real-World Task**: Query optimization translates directly to lower cloud compute bills.
- **OpenEnv Spec**: Full schema compliance, typed `SqlOptAction`/`SqlOptObservation` in `models.py`, valid `openenv.yaml`.
- **3 Tasks (Agent Graders)**: Curated query bank (`query_bank.py`) featuring `easy` (SELECT * wide tables), `medium` (Implicit joins & DISTINCT), and `hard` (N+1 correlated subqueries).
- **Meaningful Reward Function**: Returns scores mapped strictly from `0.0` to `1.0`. Provides partial progress:
  - Valid syntax (+0.2)
  - Executable without errors (+0.2)
  - Semantically correct results (+0.3)
  - Latency reduction bonus (+0.3 scaled)
- **Baseline Inference Script**: Run `python baseline_agent.py` to test a reproducible heuristic agent achieving ~0.7+ rewards.
- **Hugging Face Spaces**: Ready to deploy with `openenv push` and the included Dockerfile.

## 🛠️ Action & Observation Spaces

### Observation Space (`SqlOptObservation`)
- `original_sql` (str): The slow query.
- `schema_ddl` (str): Contextual CREATE TABLE structures.
- `current_latency_ms` (float): Baseline execution time inside Postgres.
- `explain_plan` (str): JSON output of EXPLAIN ANALYZE for the query.
- `episode_step` (int): Current step in the episode.

### Action Space (`SqlOptAction`)
- `rewritten_sql` (str): The agent's optimized string.

## 🚀 Setup & Execution

### 1. Run the Environment (Docker Rootless)
We use `docker compose` to launch a PostgreSQL sandbox and the FastAPI OpenEnv server securely.

```bash
docker compose build --no-cache api
docker compose up -d
```

### 2. Run the Baseline Agent
Test the environment endpoints using the included Python baseline inference script:

```bash
uv run baseline_agent.py
```

### 3. Deploy to Hugging Face Spaces
To push to your Hugging Face Space (requires `huggingface_hub` login):

```bash
uv run openenv push --repo-id <your-hf-username>/sql-opt-env
```