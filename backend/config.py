import os

# Shared secret — must match what the frontend sends
# Set via GCP env var, never hardcode
MASTER_KEY  = os.getenv("MASTER_KEY", "")

# GCP resources
BUCKET_NAME = os.getenv("BUCKET_NAME", "")
APP_NAME    = os.getenv("APP_NAME", "")
