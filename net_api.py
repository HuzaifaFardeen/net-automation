import yaml
import sys
import os
import requests
import json
import uuid

# --- Classes from Framework ---

class MockStubs:
    @staticmethod
    def connect_ssh(host):
        print(f"MOCK_SSH: Connecting to host {host}...")
        # Simulate some delay or check
        print("MOCK_SSH: Connection established (SIMULATED).")

    @staticmethod
    def validate_rdp(host):
        print(f"MOCK_RDP: Validating remote connection to {host}...")
        print("MOCK_RDP: Validation successful (SIMULATED).")

class APIClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()

    def login(self, login_endpoint):
        print(f"API_CLIENT: Logging in as {self.username}...")
        url = f"{self.base_url}{login_endpoint}"
        try:
            response = self.session.post(url, auth=(self.username, self.password))
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                print("API_CLIENT: Login successful. Token received.")
                return True
            else:
                print(f"API_CLIENT: Login failed. Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            print(f"API_CLIENT: Exception during login: {e}")
            return False

    def _get_headers(self):
        if not self.token:
            raise Exception("No token found. Please login first.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        print(f"API_CLIENT: GET request to {url}")
        response = self.session.get(url, headers=self._get_headers(), params=params)
        return response

    def put(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"
        print(f"API_CLIENT: PUT request to {url} with payload {payload}")
        response = self.session.put(url, headers=self._get_headers(), json=payload)
        return response

    def post(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"
        print(f"API_CLIENT: POST request to {url}")
        response = self.session.post(url, headers=self._get_headers(), json=payload)
        return response

# --- Helper Functions ---

def load_config(path):
    if not os.path.exists(path):
        print(f"Error: Config file '{path}' not found.")
        return None
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def register_user(base_url):
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "StrongPassword123!"
    
    print(f"Attempting to register user: {username}")
    
    try:
        response = requests.post(f"{base_url}/register", json={"username": username, "password": password})
        if response.status_code in [200, 201]:
            print(f"SUCCESS: Registered user '{username}' with password '{password}'")
            print("Please update your config.yaml with these credentials.")
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")

# --- Main Workflow ---

def run():
    # Check for registration flag
    if "--register" in sys.argv:
        # We need the base URL. We can try to get it from config or hardcode default if config missing
        # For simplicity, let's try to load config first, or fallback
        config = load_config("config.yaml")
        base_url = "https://semantic-brandea-banao-dc049ed0.koyeb.app"
        if config:
             base_url = config['api']['base_url']
        register_user(base_url)
        return

    print("WORKFLOW: Starting Automation Framework...")
    
    # Load Config
    config_path = "config.yaml"
    config = load_config(config_path)
    if not config:
        return # Error printed in load_config
        
    print("WORKFLOW: Configuration loaded.")

    base_url = config['api']['base_url']
    username = config['user']['username']
    password = config['user']['password']
    
    # Initialize Client
    client = APIClient(base_url, username, password)
    
    # Login
    if not client.login(config['api']['endpoints']['login']):
        print("WORKFLOW: Critical - Login failed. Exiting.")
        return

    # --- Pre-Fetcher Stage ---
    print("\n--- STAGE: PRE-FETCHER ---")
    mock_stubs = MockStubs() 
    
    # Fetch Tenants
    tenants_resp = client.get(config['api']['endpoints']['tenant'])
    tenants = tenants_resp.json() if tenants_resp.status_code == 200 else []
    print(f"PRE-FETCHER: Fetched {len(tenants)} Tenants.")

    # Fetch Service Engines
    se_resp = client.get(config['api']['endpoints']['service_engine'])
    ses = se_resp.json() if se_resp.status_code == 200 else []
    print(f"PRE-FETCHER: Fetched {len(ses)} Service Engines.")

    # Fetch Virtual Services
    vs_endpoint = config['api']['endpoints']['virtual_service']
    vs_resp = client.get(vs_endpoint)
    vss = vs_resp.json() if vs_resp.status_code == 200 else []
    print(f"PRE-FETCHER: Fetched {len(vss)} Virtual Services.")
    
    # --- Pre-Validation Stage ---
    print("\n--- STAGE: PRE-VALIDATION ---")
    mock_stubs.connect_ssh("load-balancer-01") 
    mock_stubs.validate_rdp("management-server") 

    target_vs_name = config['workflow']['target_vs_name']
    target_vs = next((vs for vs in vss if vs.get("name") == target_vs_name), None)

    if not target_vs:
        print(f"PRE-VALIDATION: Target VS '{target_vs_name}' not found. Attempting to seed it for the test...")
        # Seeding logic
        seed_payload = {
            "name": target_vs_name,
            "ip_address": "10.10.10.10",
            "enabled": True
        }
        create_resp = client.post(vs_endpoint, seed_payload)
        if create_resp.status_code in [200, 201]:
             target_vs = create_resp.json()
             print(f"PRE-VALIDATION: Seeded '{target_vs_name}' successfully.")
        else:
             print(f"PRE-VALIDATION: Failed to seed VS. {create_resp.status_code} {create_resp.text}")
             return
    else:
        print(f"PRE-VALIDATION: Found VS '{target_vs_name}'.")

    # Now validate it is enabled
    vs_uuid = target_vs.get("id")
    print(f"PRE-VALIDATION: VS UUID is {vs_uuid}")
    
    # Re-fetch specific VS to be sure
    specific_vs_resp = client.get(f"{vs_endpoint}/{vs_uuid}")
    if specific_vs_resp.status_code != 200:
        print(f"PRE-VALIDATION: Failed to fetch VS {vs_uuid}")
        return
        
    current_vs = specific_vs_resp.json()
    
    if current_vs.get("enabled") is True:
        print("PRE-VALIDATION: Success - 'enabled' is True.")
    else:
        print(f"PRE-VALIDATION: Warning - 'enabled' is {current_vs.get('enabled')}. Resetting to True requires ensuring test state.")
        # Optional: Reset to true if needed, but for now we proceed or fail.
        # Let's assume we want to reset it for the test to be valid trigger test
        if current_vs.get("enabled") is False:
             print("PRE-VALIDATION: Resetting VS to enabled: True for test...")
             reset_resp = client.put(f"{vs_endpoint}/{vs_uuid}", {"enabled": True})
             if reset_resp.status_code == 200:
                 print("PRE-VALIDATION: Reset successful.")
             else:
                 print("PRE-VALIDATION: Reset failed. Proceeding anyway.")

    # --- Task / Trigger Stage ---
    print("\n--- STAGE: TASK/TRIGGER ---")
    print(f"TRIGGER: Disabling Virtual Service {vs_uuid}...")
    
    update_payload = {"enabled": False}
    update_resp = client.put(f"{vs_endpoint}/{vs_uuid}", update_payload)
    
    if update_resp.status_code == 200:
        updated_data = update_resp.json()
        print(f"TRIGGER: Update request successful. Response enabled state: {updated_data.get('enabled')}")
    else:
        print(f"TRIGGER: Update failed. {update_resp.status_code} {update_resp.text}")

    # --- Post-Validation Stage ---
    print("\n--- STAGE: POST-VALIDATION ---")
    verify_resp = client.get(f"{vs_endpoint}/{vs_uuid}")
    if verify_resp.status_code == 200:
        final_vs = verify_resp.json()
        if final_vs.get("enabled") is False:
             print("POST-VALIDATION: Success - Virtual Service is disabled.")
        else:
             print(f"POST-VALIDATION: Failure - Virtual Service is still enabled ({final_vs.get('enabled')}).")
    else:
        print("POST-VALIDATION: Error fetching VS.")

if __name__ == "__main__":
    run()
