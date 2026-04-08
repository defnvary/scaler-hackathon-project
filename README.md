# SQL Query Optimizer OpenEnv

## Environment Description and Motivation
The **SQL Query Optimizer** OpenEnv is an RL environment built for the Meta × PyTorch OpenEnv Hackathon 2026. The agent's task is to receive a slow SQL query and schema, and rewrite it into an optimized version.

**Motivation (Real-World Task Simulation):**
Query optimization translates directly to lower cloud compute bills and improved software performance. Identifying implicit cross joins, redundant scans, and N+1 anti-patterns in production schemas is a task DBAs and backend engineers perform daily. Rather than a toy game, this environment evaluates an agent’s capability to parse, reason, and rewrite actual `PostgreSQL` dialects while actively benchmarking the result set and latency.

## Action and Observation Space Definitions

### Observation Space (`SqlOptObservation`)
- `original_sql` (str): The slow query to be optimized.
- `schema_ddl` (str): Contextual CREATE TABLE statements and indices.
- `current_latency_ms` (float): Baseline execution time measured inside the Sandbox Postgres DB.
- `explain_plan` (str): JSON output of EXPLAIN ANALYZE for the query.
- `episode_step` (int): Current step in the episode.

### Action Space (`SqlOptAction`)
- `rewritten_sql` (str): The agent's optimized query string.

## Task Descriptions and Expected Difficulty
The environment uses a `query_bank.py` to randomly serve tasks across three categories:
1. **Easy**: (e.g., `SELECT *` on wide tables). The agent must learn to select only the necessary columns based on a given context.
2. **Medium**: (e.g., Implicit Cross Joins & Redundant `DISTINCT`). The agent must recognize legacy join syntax, convert it to explicit `INNER JOIN` logic, and remove unnecessary aggregations.
3. **Hard**: (e.g., Correlated Subqueries / N+1 patterns). The agent must flatten `SELECT (SELECT COUNT(...) FROM ... WHERE ...)` logic into a grouped `LEFT JOIN` to prevent row-by-row execution.

**Agent Graders & Meaningful Reward Function:**
The reward strictly outputs between `0.0` and `1.0` (with partial progress):
- **+0.2** for valid `sqlglot` Postgres syntax.
- **+0.2** if the query is executable on the Sandbox Postgres instance (no runtime errors).
- **+0.3** if the result set is semantically identical to the baseline (MD5 hashing).
- **+0.3** (scaled) based on `(baseline_ms - new_ms) / baseline_ms`.

## Setup and Usage Instructions

### 1. Run the Environment (Containerized execution)
The environment contains a fully working `Dockerfile` and `docker-compose.yml` to launch a PostgreSQL sandbox alongside the FastAPI OpenEnv server securely.

```bash
# Build and run the local instances
docker compose build --no-cache api
docker compose up -d
```

### 2. Run the Baseline Inference Script
To produce reproducible baseline scores using the `OpenAI` client standard:

```bash
# Ensure dependencies are available (e.g., via uv sync)
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o"
export OPENAI_API_KEY="sk-..."

# Run the strict stdout format inference script
uv run inference.py
```

### 3. Deploy to Hugging Face Spaces
To push to your Hugging Face Space (requires `huggingface_hub` login):

```bash
uv run openenv push --repo-id <your-hf-username>/sql-opt-env
```

## Baseline Scores
Running `inference.py` directly executes the environment logic against the query bank. Baseline runs yield a deterministic reproducible score ranging from **~0.400** to **0.700+** when testing the built-in heuristic/LLM mocks, demonstrating the partial reward signals and accuracy metrics functioning exactly as specified.