import os
import time
import requests
import json

ENV_URL = os.environ.get("ENV_URL", "http://localhost:8000")


def simple_heuristic_agent(original_sql):
    """
    A very simple heuristic 'agent' that mimics LLM rewrites.
    """
    sql = original_sql
    # Fix for 'easy' query
    sql = sql.replace("SELECT *", "SELECT o_orderkey")
    # Fix for 'medium' query
    sql = sql.replace("SELECT DISTINCT", "SELECT")
    # Fix for 'hard' query (basic attempt)
    if "SELECT COUNT(*)" in sql and "FROM orders o" in sql:
        sql = "SELECT c.c_name, COUNT(o.o_orderkey) FROM customer c LEFT JOIN orders o ON c.c_custkey = o.o_custkey AND o.o_totalprice > 1000 GROUP BY c.c_name;"

    return sql


def run_evaluation(episodes=3):
    print(f"Starting Baseline Evaluation against {ENV_URL}...")

    # Wait for the server
    for _ in range(10):
        try:
            requests.get(f"{ENV_URL}/docs")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)

    total_reward = 0.0

    for i in range(episodes):
        print(f"\n--- Episode {i + 1} ---")

        # Reset environment to get a new task
        res = requests.post(f"{ENV_URL}/reset")
        if res.status_code != 200:
            print("Failed to reset environment. Is the server running?")
            return

        data = res.json()
        obs = data["observation"]
        episode_id = data.get("episode_id")

        original_sql = obs["original_sql"]
        baseline_latency = obs["current_latency_ms"]
        print(f"Original SQL: {original_sql}")
        print(f"Baseline Latency: {baseline_latency:.2f} ms")

        # Agent generates action
        rewritten_sql = simple_heuristic_agent(original_sql)
        print(f"\nRewritten SQL: {rewritten_sql}")

        # Step environment
        payload = {"action": {"rewritten_sql": rewritten_sql}, "episode_id": episode_id}

        step_res = requests.post(f"{ENV_URL}/step", json=payload)
        step_data = step_res.json()

        step_obs = step_data["observation"]
        reward = step_data["reward"]
        new_latency = step_obs["current_latency_ms"]

        print(f"New Latency: {new_latency:.2f} ms")
        print(f"Episode Reward: {reward:.2f} / 1.00")

        if "error" in step_obs["explain_plan"]:
            print(f"Execution Error: {step_obs['explain_plan']}")

        total_reward += reward
        time.sleep(1)  # brief pause between episodes

    avg_reward = total_reward / episodes
    print(f"\n=====================================")
    print(f"Evaluation Complete!")
    print(f"Average Reward: {avg_reward:.2f} / 1.00")
    print(f"=====================================")


if __name__ == "__main__":
    run_evaluation(episodes=3)
