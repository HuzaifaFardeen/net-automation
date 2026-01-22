# Python Test Automation Framework

This framework automates the validation of a mock load balancer API.

## Setup

1. **Prerequisites**: Ensure you have Python installed.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration & Usage

### 1. Registration (Optional)
If you need a new user, you can run the script with the `--register` flag:
```bash
python main.py --register
```
This will print a new username and password. Update `config.yaml` with these credentials.

### 2. Configuration
Ensure `config.yaml` is in the same directory and contains your valid `username` and `password`.

### 3. Run Automation
Run the main test workflow:
```bash
python main.py
```

## Workflow Details
1. **Pre-Fetcher**: Fetches Tenants, Service Engines, ES.
2. **Pre-Validation**: Checks for target VS. Seeds it if missing.
3. **Trigger**: Disables the VS.
4. **Post-Validation**: Verifies VS is disabled.
