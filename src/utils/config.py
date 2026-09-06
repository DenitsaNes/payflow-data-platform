"""PayFlow — shared configuration."""

import os
from datetime import datetime
from pathlib import Path

# Processing date used for "future timestamp" validation.
# The synthetic dataset covers September 2026.
MAX_TRANSACTION_DATE = datetime(2026, 9, 30)

# Database connection settings
DB_HOST = os.getenv("PAYFLOW_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("PAYFLOW_DB_PORT", "3307"))
DB_USER = os.getenv("PAYFLOW_DB_USER", "payflow")
DB_PASSWORD = os.getenv("PAYFLOW_DB_PASSWORD", "payflow")
DB_NAME = os.getenv("PAYFLOW_DB_NAME", "payflow")

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REJECTED_DIR = DATA_DIR / "rejected"

# Database connection string for SQLAlchemy
DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
