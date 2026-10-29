# SafeShop - Integrated Watering-Hole Attack Detection Laboratory

Both websites integrated in one project with centralized logging.

## Architecture
- sites/legitimate/ - Legitimate SafeShop (Flask, port 5000)
- sites/suspicious/ - Simulated compromised/suspicious site (Flask, port 5001)
- shared/web_logger.py - Centralized CSV logger writing to logs/web_logs.csv
- Both sites log to the same CSV with site_identifier 'legitimate' or 'suspicious'

## Setup
`powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
`

## Run both websites
`powershell
python run_both.py
`
Or run separately:
`powershell
# Terminal 1
cd sites\legitimate
="..\.."
python app.py

# Terminal 2
cd sites\suspicious
="..\.."
="true"
python app.py
`

## URLs
- Legitimate: http://127.0.0.1:5000
- Suspicious: http://127.0.0.1:5001

## Centralized logs
- logs/web_logs.csv (created automatically)
Fields: timestamp, site_identifier, http_method, requested_path, http_status_code, client_ip_address, user_agent, referrer, request_id

## Test scenarios
- Normal request to legitimate: GET http://127.0.0.1:5000/
- Navigate to another page: GET http://127.0.0.1:5000/products
- Request to suspicious: GET http://127.0.0.1:5001/
- Simulated redirect (local): GET http://127.0.0.1:5001/lab-test/redirect (returns 302)
- Repeated requests: curl/refresh /lab-test/repeat multiple times
- Unexpected resource (local mock): GET http://127.0.0.1:5001/lab-test/resources/unapproved.js
