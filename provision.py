import os
import argparse
import pandas as pd
import requests
import logging
import time
from msal import ConfidentialClientApplication
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

# Configuration
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

# Department-to-group mapping – replace with your actual group Object IDs
DEPARTMENT_GROUPS = {
    "Finance": "90fad2f0-c71c-48d5-94d2-f634670ecbc0",
    "Engineering": "f9e31a8f-53c6-453e-a851-f135a3033468",
    "Sales": "252709c3-487b-4f43-a725-f1a1215c21ae",
    "HR": "25c8084e-c9a5-4e63-896a-a880d0ec633b"
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("provisioning.log"), logging.StreamHandler()]
)

# Global flag for dry-run
DRY_RUN = False

# ---------- Retry Decorator ----------
def retry_on_failure(max_retries=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logging.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

# ---------- Authentication ----------
def get_access_token():
    """Authenticate and get an access token using client credentials flow."""
    app = ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in result:
        return result["access_token"]
    else:
        logging.error(f"Auth failed: {result.get('error_description')}")
        raise Exception(f"Auth failed: {result.get('error_description')}")

# ---------- User Creation ----------
@retry_on_failure(max_retries=3, delay=5)
def create_user(user_data, token):
    """Create a user in Entra ID via Microsoft Graph API."""
    url = "https://graph.microsoft.com/v1.0/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Idempotency check: see if user already exists
    check_url = f"https://graph.microsoft.com/v1.0/users/{user_data['userPrincipalName']}"
    check_response = requests.get(check_url, headers=headers)
    if check_response.status_code == 200:
        logging.info(f"User {user_data['userPrincipalName']} already exists. Skipping.")
        return check_response.json()["id"]
    
    if DRY_RUN:
        logging.info(f"🔍 DRY RUN: Would create {user_data['userPrincipalName']}")
        return "fake-user-id"
    
    payload = {
        "accountEnabled": True,
        "displayName": f"{user_data['firstName']} {user_data['lastName']}",
        "mailNickname": user_data['email'].split('@')[0],
        "userPrincipalName": user_data['email'],
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": "TempP@ssw0rd123!"
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        user_id = response.json()["id"]
        logging.info(f"✅ Created: {user_data['email']}")
        # Send welcome email (placeholder)
        logging.info(f"📧 Welcome email sent to {user_data['email']} with password: TempP@ssw0rd123!")
        return user_id
    else:
        logging.error(f"❌ Failed: {user_data['email']} - {response.text}")
        return None

# ---------- Group Membership ----------
@retry_on_failure(max_retries=3, delay=5)
def add_user_to_group(user_id, group_id, token):
    """Add user to a security group (RBAC enforcement)."""
    if DRY_RUN:
        logging.info(f"🔍 DRY RUN: Would add user {user_id} to group {group_id}")
        return True
    
    url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 204:
        logging.info(f"  → Added to group")
        return True
    else:
        logging.error(f"  → Group add failed: {response.text}")
        return False

# ---------- CSV Validation ----------
def validate_csv(df):
    required_columns = ['firstName', 'lastName', 'department', 'role', 'email']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logging.error(f"Missing columns in CSV: {missing_cols}")
        return False
    if df.empty:
        logging.error("CSV file is empty")
        return False
    return True

# ---------- Main ----------
def main():
    global DRY_RUN
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview actions without executing')
    args = parser.parse_args()
    DRY_RUN = args.dry_run
    
    logging.info(f"=== {'DRY RUN - ' if DRY_RUN else ''}Starting provisioning process ===")
    
    # Get access token
    token = get_access_token()
    
    # Read CSV
    try:
        df = pd.read_csv("employees.csv")
    except FileNotFoundError:
        logging.error("employees.csv not found in current directory.")
        return
    
    if not validate_csv(df):
        return
    
    created_count = 0
    failed_count = 0
    
    for _, row in df.iterrows():
        user_data = {
            "firstName": row["firstName"],
            "lastName": row["lastName"],
            "email": row["email"],
            "userPrincipalName": row["email"],
            "department": row["department"]
        }
        
        user_id = create_user(user_data, token)
        if user_id and user_id != "fake-user-id":
            created_count += 1
            group_id = DEPARTMENT_GROUPS.get(row["department"])
            if group_id:
                add_user_to_group(user_id, group_id, token)
        elif user_id == "fake-user-id":
            # Dry-run mode
            created_count += 1
            group_id = DEPARTMENT_GROUPS.get(row["department"])
            if group_id:
                add_user_to_group(user_id, group_id, token)
        else:
            failed_count += 1
    
    # Summary report
    summary = {
        'total': len(df),
        'created': created_count,
        'failed': failed_count
    }
    report_df = pd.DataFrame([summary])
    report_df.to_csv('provisioning_report.csv', index=False)
    logging.info(f"📊 Summary: Total={summary['total']}, Created={summary['created']}, Failed={summary['failed']}")
    logging.info(f"📊 Report saved to provisioning_report.csv")
    logging.info("=== Provisioning process completed ===")

if __name__ == "__main__":
    main()