"""Constants for the application"""

# Cache Settings
CACHE_TIMEOUT_SECONDS = 60

# Frontend Settings
FRONTEND_REFRESH_INTERVAL_MS = 30000  # 30 seconds

# Dashboard Settings
TRANSACTION_TABLE_MAX_HEIGHT = 520  # pixels
TRANSACTION_DEFAULT_LIMIT = 50
TRENDS_DEFAULT_DAYS = 7
MONTHLY_COMPARISON_DEFAULT_MONTHS = 3

# API Settings
API_DEFAULT_PORT = 8001
CORS_ALLOWED_ORIGINS = ["http://localhost:*", "http://127.0.0.1:*"]  # For production, specify exact origins

# Google Sheets Settings
SHEETS_RETRY_ATTEMPTS = 3
SHEETS_RETRY_DELAY_SECONDS = 2

# PDF Export Settings
PDF_FONT = "Helvetica"
PDF_FONT_SIZE_TITLE = 14
PDF_FONT_SIZE_NORMAL = 11
PDF_FONT_SIZE_SMALL = 10
PDF_TABLE_COL_WIDTHS = [30, 25, 85, 40]

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
