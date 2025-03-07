import dropbox
from datetime import datetime
import os
import schedule
import time

# Replace this with your actual Dropbox access token
DROPBOX_ACCESS_TOKEN = "sl.CCIUixUaL9gBYwOykS1DrlhR7CoS_4CpYe5iCFTyK3RrGdB37mtkTY6pH3EyxiQ1fzMvhZe61JCVe5B22YKpW_nDhSKHoDLldIqqKwf0TitOA5DKO0mEtRGfMwptcgnzFGmt85lKqJzu"

# Function to upload a file to Dropbox
def upload_to_dropbox(local_path, dropbox_path):
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        with open(local_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        #print(f"Backup successful: {local_path} -> {dropbox_path}")
    except Exception as e:
        print(f"Failed to upload {local_path} to Dropbox: {e}")

# Function to back up the customer.csv and history_log.csv files
def backup_files():
    # Get current date for naming the backup files
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Define file paths
    customer_file = "customer.csv"
    history_log_file = "history_log.csv"

    # Dropbox backup paths
    dropbox_customer_path = f"/backups/customer_backup_{current_date}.csv"
    dropbox_history_path = f"/backups/history_log_backup_{current_date}.csv"

    # Upload to Dropbox
    if os.path.exists(customer_file):
        upload_to_dropbox(customer_file, dropbox_customer_path)
    else:
        print(f"File not found: {customer_file}")

    if os.path.exists(history_log_file):
        upload_to_dropbox(history_log_file, dropbox_history_path)
    else:
        print(f"File not found: {history_log_file}")

# Schedule weekly backups
def weekly_backup():
    schedule.every().week.do(backup_files)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Manual trigger for testing
if __name__ == "__main__":
    #print("Starting manual backup for testing...")
    backup_files()  # Test immediate backup
    #print("Manual backup complete.")
