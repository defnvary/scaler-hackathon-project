import asyncio
import os
import textwrap
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from sql_opt_env.client import SqlOptEnv
from sql_opt_env.models import SqlOptAction

API_KEY = (
    os.getenv("HF_TOKEN")
    or os.getenv("API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or "sk-dummy"
)
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
TASK_NAME = os.getenv("SQL_OPT_ENV_TASK", "optimize")
BENCHMARK = os.getenv("SQL_OPT_ENV_BENCHMARK", "sql_opt_env")
MAX_STEPS = 1  # our environment is designed to be completed in 1 step

# Threshold and normalization
SUCCESS_SCORE_THRESHOLD = 0.5
MAX_TOTAL_REWARD = 1.0

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert PostgreSQL database administrator. Your task is to rewrite the provided slow SQL query into an optimized version.
    - Ensure your syntax is valid PostgreSQL.
    - Avoid changing the semantic meaning of the result set.
    - Reply with exactly one message containing the raw optimized SQL string (no markdown ticks, no extra text).
    """
).strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: Optional[str]
) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Safely escape newlines in action for logging
    safe_action = action.replace("\n", " ")
    print(
        f"[STEP] step={step} action={safe_action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def build_user_prompt(schema_ddl: str, original_sql: str) -> str:
    return textwrap.dedent(
        f"""
        Schema DDL:
        {schema_ddl}
        
        Original Slow SQL:
        {original_sql}
        
        Please provide the optimized SQL:
        """
    ).strip()


def get_model_message(client: OpenAI, schema_ddl: str, original_sql: str) -> str:
    user_prompt = build_user_prompt(schema_ddl, original_sql)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=250,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        # Remove markdown if the model hallucinates it
        if text.startswith("```sql"):
            text = text[6:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "SELECT 1;"


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Connect via HTTP since Docker is handled locally or via from_docker_image
    # We will connect to the localhost endpoint where the API is running for testing.
    # The actual hackathon evaluation might use a different connect mechanism.

    # Use synchronous EnvClient context wrapper (the example uses async await, but OpenEnv provides synchronous context)
    # Our generated SqlOptEnv is synchronous from the scaffold.
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        if os.getenv("IMAGE_NAME"):
            env = await SqlOptEnv.from_docker_image(os.getenv("IMAGE_NAME"))
        else:
            env = SqlOptEnv(base_url="http://localhost:8000")
            await env.connect()

        result = await env.reset()
        obs = result.observation

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            rewritten_sql = get_model_message(client, obs.schema_ddl, obs.original_sql)

            # Simple fallback heuristic for baseline testing if OpenAI fails (mock fallback)
            if rewritten_sql == "SELECT 1;":
                rewritten_sql = obs.original_sql.replace("SELECT DISTINCT", "SELECT")

            result = await env.step(SqlOptAction(rewritten_sql=rewritten_sql))
            obs = result.observation

            reward = result.reward or 0.0
            done = result.done

            error = None
            if "error" in obs.explain_plan:
                error = "SQL Execution Error"

            rewards.append(reward)
            steps_taken = step

            log_step(
                step=step, action=rewritten_sql, reward=reward, done=done, error=error
            )

            if done:
                break

        score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)  # clamp to [0, 1]
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Runtime Error: {e}", flush=True)
    finally:
        try:
            await env.close()
        except:
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    asyncio.run(main())
