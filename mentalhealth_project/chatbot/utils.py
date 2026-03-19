import requests

def get_health_data():
    url = "https://api.sahha.ai/v1/health"  # example endpoint

    headers = {
        "Authorization": "https://sandbox-api.sahha.ai/api/v1/profile/score/?endDateTime=2026-03-18&startDateTime=2026-03-12"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return None

    except:
        return None