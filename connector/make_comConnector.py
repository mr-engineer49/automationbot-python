import requests

class MakeConnector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.make.com/v2"

    def get_scenarios(self):
        r = requests.get(f"{self.base_url}/scenarios", headers={"Authorization": f"Token {self.api_key}"})
        return r.json()

    def run_scenario(self, scenario_id):
        r = requests.post(f"{self.base_url}/scenarios/{scenario_id}/run", headers={"Authorization": f"Token {self.api_key}"})
        return r.json()
