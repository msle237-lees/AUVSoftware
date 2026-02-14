import requests

def run_create(run_name: str = "test1", platform: str = "linux", vehicle:str = "string", operator:str = "user", notes:str = "none", config:str = "none") -> dict:
    """
    Create a new run in the database by sending a POST request to the /runs endpoint.
    """
    api_base_url = "http://localhost:8000"
    runs_endpoint = "/runs"
    url = f"{api_base_url}{runs_endpoint}"
    
    payload = {
        "name": run_name,
        "platform": platform,
        "vehicle": vehicle,
        "operator": operator,
        "notes": notes,
        "config_json": config
        }
    
    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()  # Raise an error for bad status codes
        data = resp.json()
        print(f"Run created successfully: {data}")
    
        return data
    except requests.RequestException as e:
        print(f"Failed to create run: {e}")
        return {}
        
    
if __name__ == "__main__":
    run_create()
    