import requests
import json
import time

URL = "http://localhost:8000"


def test_env():
    # Wait for the API to boot
    for _ in range(10):
        try:
            r = requests.get(f"{URL}/docs")
            if r.status_code == 200:
                print("API is up!")
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        print("API failed to start")
        return

    print("\n--- Testing /reset ---")
    reset_resp = requests.post(f"{URL}/reset")
    print(reset_resp.status_code)
    try:
        obs = reset_resp.json()
        print(json.dumps(obs, indent=2))
        episode_id = obs.get("episode_id")
    except Exception as e:
        print(f"Failed to parse /reset response: {reset_resp.text}")
        return

    print("\n--- Testing /step ---")
    action_payload = {
        "action": {"rewritten_sql": "SELECT * FROM dummy WHERE id = 1 LIMIT 1;"},
        "episode_id": episode_id,
    }
    step_resp = requests.post(f"{URL}/step", json=action_payload)
    print(step_resp.status_code)
    try:
        print(json.dumps(step_resp.json(), indent=2))
    except Exception as e:
        print(f"Failed to parse /step response: {step_resp.text}")


if __name__ == "__main__":
    test_env()
