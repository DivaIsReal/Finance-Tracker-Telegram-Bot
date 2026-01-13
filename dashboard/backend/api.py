import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta, date, timezone
import secrets

# Timezone Indonesia (WIB)
WIB = timezone(timedelta(hours=7))
from typing import List, Dict
import os
from dotenv import load_dotenv
import time
from io import BytesIO
from fpdf import FPDF
from pathlib import Path

# Load environment from root
load_dotenv('../../.env')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==========================================
# SECURITY CONFIGURATION
# ==========================================
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'

# Validate required environment variables
REQUIRED_ENV_VARS = ['SPREADSHEET_ID', 'GOOGLE_CREDENTIALS_FILE']
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

app = FastAPI(
    title="Finance Dashboard API", 
    version="1.0",
    docs_url="/docs" if not IS_PRODUCTION else None,  # Disable docs in production
    redoc_url="/redoc" if not IS_PRODUCTION else None
)

# Serve static files (HTML frontend)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')
if os.path.exists(FRONTEND_DIR):
    app.mount("/dashboard", StaticFiles(directory=FRONTEND_DIR, html=True), name="dashboard")
    logger.info(f"✅ Dashboard frontend mounted at /dashboard from {FRONTEND_DIR}")
else:
    logger.warning(f"⚠️ Frontend directory not found: {FRONTEND_DIR}")

# ==========================================
# CORS SECURITY - Strict origins only
# ==========================================
cors_origins_str = os.getenv('CORS_ORIGINS', '')

if IS_PRODUCTION:
    # Production: Must specify exact origins, no wildcards
    if not cors_origins_str or cors_origins_str == '*':
        logger.error("❌ SECURITY: CORS_ORIGINS must be explicitly set in production!")
        raise RuntimeError("CORS_ORIGINS not properly configured for production")
    ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_str.split(',')]
else:
    # Development: Allow localhost/127.0.0.1
    if cors_origins_str and cors_origins_str != '*':
        ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_str.split(',')]
    else:
        ALLOWED_ORIGINS = [
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:5500",
            "http://127.0.0.1:5500"
        ]

logger.info(f"🔒 CORS allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to needed methods only
    allow_headers=["Content-Type", "Authorization"],  # Specific headers only
)

# Add trusted host middleware for production
if IS_PRODUCTION:
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
    if ALLOWED_HOSTS and ALLOWED_HOSTS[0]:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=[host.strip() for host in ALLOWED_HOSTS]
        )
        logger.info(f"🔒 Trusted hosts: {ALLOWED_HOSTS}")

# Google Sheets Setup
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
# Path relative from root directory
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '../..', os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'))

# Validate credentials file exists
if not os.path.exists(CREDENTIALS_FILE):
    logger.error(f"❌ SECURITY: Credentials file not found: {CREDENTIALS_FILE}")
    raise RuntimeError(f"Credentials file not found: {CREDENTIALS_FILE}")

# ==========================================
# SECURITY HEADERS
# ==========================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # XSS Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HTTPS only in production
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com"
    
    return response

# ==========================================
# RATE LIMITING (Simple in-memory)
# ==========================================
_rate_limit_store = {}
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # seconds

def check_rate_limit(client_ip: str) -> bool:
    """Simple rate limiting check"""
    now = time.time()
    
    # Clean old entries
    _rate_limit_store[client_ip] = [
        timestamp for timestamp in _rate_limit_store.get(client_ip, [])
        if now - timestamp < RATE_LIMIT_WINDOW
    ]
    
    # Check limit
    if len(_rate_limit_store.get(client_ip, [])) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []
    _rate_limit_store[client_ip].append(now)
    
    return True

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting"""
    client_ip = request.client.host
    
    if not check_rate_limit(client_ip):
        logger.warning(f"⚠️ Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )
    
    return await call_next(request)

# ==========================================
# SECURE ERROR HANDLING
# ==========================================
def get_safe_error_message(error: Exception, context: str = "") -> str:
    """
    Get safe error message for client.
    In production, hide sensitive details.
    """
    if IS_PRODUCTION:
        # Generic message in production
        logger.error(f"Error in {context}: {str(error)}", exc_info=True)
        return f"An error occurred while processing {context}. Please try again later."
    else:
        # Detailed message in development
        return f"Error in {context}: {str(error)}"

# ==========================================
# INPUT VALIDATION
# ==========================================
def validate_positive_integer(value: int, name: str, max_value: int = 1000) -> int:
    """Validate positive integer with upper bound"""
    if not isinstance(value, int) or value < 1:
        raise HTTPException(status_code=400, detail=f"{name} must be a positive integer")
    if value > max_value:
        raise HTTPException(status_code=400, detail=f"{name} cannot exceed {max_value}")
    return value

# ==========================================
# CACHE SYSTEM
# ==========================================
_cache = {}
_cache_timeout = 60  # Cache 60 seconds

def get_cached_data():
    """Get data from cache or fetch new from Google Sheets"""
    now = time.time()
    
    # Check if cache exists and is still valid
    if '_data' in _cache and '_timestamp' in _cache:
        cache_age = now - _cache['_timestamp']
        if cache_age < _cache_timeout:
            logger.debug(f"✅ Using cached data (age: {int(cache_age)}s)")
            return _cache['_data']
    
    # Fetch fresh data
    logger.info("🔄 Fetching fresh data from Google Sheets...")
    data = get_sheet_data()
    
    # Update cache
    _cache['_data'] = data
    _cache['_timestamp'] = now
    
    return data

def get_sheet_data():
    """Get data from Google Sheets"""
    try:
        # Don't log sensitive credentials info in production
        if not IS_PRODUCTION:
            logger.debug(f"📂 Credentials file: {CREDENTIALS_FILE}")
            logger.debug(f"📊 Spreadsheet ID: {SPREADSHEET_ID}")
        
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_FILE, 
            scope
        )
        
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.sheet1
        
        # Get all records
        records = sheet.get_all_records()
        
        logger.info(f"✅ Fetched {len(records)} records from Google Sheets")
        return records
        
    except FileNotFoundError as e:
        logger.error(f"❌ Credentials file not found")
        raise HTTPException(
            status_code=500, 
            detail=get_safe_error_message(e, "loading credentials")
        )
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error(f"❌ Spreadsheet not found or no access")
        raise HTTPException(
            status_code=500,
            detail="Spreadsheet not found or access denied"
        )
    except Exception as e:
        logger.error(f"❌ Error fetching from Sheets: {type(e).__name__}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=get_safe_error_message(e, "fetching data")
        )


def parse_date_ddmmyyyy(value: str) -> date:
    day, month, year = map(int, value.split('/'))
    return date(year, month, day)


def filter_records_by_range(records: List[Dict], start: date, end: date) -> List[Dict]:
    filtered = []
    for record in records:
        date_str = record.get('Tanggal', '')
        if not date_str:
            continue
        try:
            d = parse_date_ddmmyyyy(date_str)
            if start <= d <= end:
                filtered.append(record)
        except:
            continue
    return filtered


def compute_totals(records: List[Dict]) -> Dict:
    pemasukan = 0.0
    pengeluaran = 0.0
    for r in records:
        tipe = r.get('Tipe', '')
        try:
            amount = float(r.get('Jumlah', 0))
        except:
            amount = 0
        if tipe == 'Pemasukan':
            pemasukan += amount
        elif tipe == 'Pengeluaran':
            pengeluaran += abs(amount)
    return {
        "pemasukan": pemasukan,
        "pengeluaran": pengeluaran,
        "net": pemasukan - pengeluaran
    }


def build_pdf(records: List[Dict], period_label: str) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Laporan Transaksi', ln=1)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 8, f'Periode: {period_label}', ln=1)
    generated_at = datetime.now(tz=WIB).strftime('%d/%m/%Y %H:%M')
    pdf.cell(0, 8, f'Digenerate: {generated_at}', ln=1)
    pdf.ln(2)

    totals = compute_totals(records)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'Ringkasan', ln=1)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, f'Total Pemasukan : Rp {totals["pemasukan"]:,.0f}', ln=1)
    pdf.cell(0, 7, f'Total Pengeluaran: Rp {totals["pengeluaran"]:,.0f}', ln=1)
    pdf.cell(0, 7, f'Selisih          : Rp {totals["net"]:,.0f}', ln=1)
    pdf.ln(4)

    # Table header
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(30, 8, 'Tanggal', border=1)
    pdf.cell(25, 8, 'Kategori', border=1)
    pdf.cell(85, 8, 'Keterangan', border=1)
    pdf.cell(40, 8, 'Jumlah', border=1, ln=1)

    pdf.set_font('Helvetica', '', 10)
    for r in records:
        tanggal = r.get('Tanggal', '')
        waktu = r.get('Waktu', '')
        kategori = r.get('Kategori', '')
        ket = r.get('Keterangan', '')
        try:
            amt = float(r.get('Jumlah', 0))
        except:
            amt = 0
        amount_text = f"{'-' if amt < 0 else '+'} Rp {abs(amt):,.0f}"

        # Cells
        pdf.cell(30, 8, f"{tanggal}\n{waktu}" if waktu else tanggal, border=1)
        pdf.cell(25, 8, kategori[:14], border=1)
        pdf.cell(85, 8, ket[:50], border=1)
        pdf.cell(40, 8, amount_text, border=1, ln=1)

    if not records:
        pdf.cell(0, 8, 'Tidak ada data untuk periode ini.', ln=1)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer


@app.get("/")
def root():
    """Root endpoint - redirects to dashboard"""
    return {
        "message": "Finance Dashboard API",
        "version": "1.0",
        "dashboard": "http://localhost:8001/dashboard",
        "endpoints": {
            "summary": "/api/summary",
            "transactions": "/api/transactions",
            "trends": "/api/trends",
            "categories": "/api/categories",
            "export_pdf": "/api/export/pdf"
        }
    }


@app.get("/api/summary")
def get_summary():
    """Get summary statistics for current month"""
    try:
        records = get_cached_data()  # Use cache for better performance
        
        # Get current month
        now = datetime.now(tz=WIB)
        current_month = now.month
        current_year = now.year
        
        pemasukan = 0
        pengeluaran = 0
        
        for record in records:
            # Parse date (format: DD/MM/YYYY)
            date_str = record.get('Tanggal', '')
            if not date_str:
                continue
                
            try:
                day, month, year = map(int, date_str.split('/'))
                trans_date = datetime(year, month, day)
                
                # Filter current month
                if trans_date.month == current_month and trans_date.year == current_year:
                    tipe = record.get('Tipe', '')
                    jumlah = float(record.get('Jumlah', 0))
                    
                    if tipe == 'Pemasukan':
                        pemasukan += jumlah
                    elif tipe == 'Pengeluaran':
                        pengeluaran += abs(jumlah)
            except (ValueError, TypeError):
                continue
        
        saving = pemasukan - pengeluaran
        saving_percent = (saving / pemasukan * 100) if pemasukan > 0 else 0
        
        return {
            "pemasukan": pemasukan,
            "pengeluaran": pengeluaran,
            "saving": saving,
            "saving_percent": round(saving_percent, 1),
            "month": now.strftime("%B %Y")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_summary", exc_info=True)
        raise HTTPException(status_code=500, detail=get_safe_error_message(e, "summary"))


@app.get("/api/transactions")
def get_transactions(limit: int = 50):
    """Get recent transactions"""
    try:
        # Validate input
        limit = validate_positive_integer(limit, "limit", max_value=500)
        
        records = get_cached_data()  # Use cache
        
        # Sort by date (newest first) and limit
        transactions = []
        for record in records:
            try:
                transactions.append({
                    "tanggal": str(record.get('Tanggal', ''))[:10],  # Limit length
                    "waktu": str(record.get('Waktu', ''))[:8],
                    "tipe": str(record.get('Tipe', ''))[:20],
                    "kategori": str(record.get('Kategori', ''))[:50],
                    "jumlah": float(record.get('Jumlah', 0)),
                    "keterangan": str(record.get('Keterangan', ''))[:200],  # Limit
                    "detail": str(record.get('Detail', ''))[:500]  # Limit
                })
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing record: {e}")
                continue
        
        # Reverse to get newest first
        transactions = transactions[-limit:][::-1]
        
        return {
            "transactions": transactions,
            "total": len(transactions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_transactions", exc_info=True)
        raise HTTPException(status_code=500, detail=get_safe_error_message(e, "transactions"))


@app.get("/api/trends")
def get_trends(days: int = 7):
    """Get spending trends for last N days"""
    try:
        # Validate input
        days = validate_positive_integer(days, "days", max_value=365)
        
        records = get_cached_data()
        
        # Calculate daily expenses for last N days
        daily_data = {}
        
        for i in range(days):
            date = datetime.now(tz=WIB) - timedelta(days=i)
            date_str = date.strftime('%d/%m/%Y')
            daily_data[date_str] = {
                "date": date.strftime('%d %b'),
                "amount": 0
            }
        
        for record in records:
            date_str = record.get('Tanggal', '')
            if date_str in daily_data:
                tipe = record.get('Tipe', '')
                if tipe == 'Pengeluaran':
                    try:
                        jumlah = abs(float(record.get('Jumlah', 0)))
                        daily_data[date_str]["amount"] += jumlah
                    except (ValueError, TypeError):
                        continue
        
        # Convert to list and sort by date
        trends = list(daily_data.values())
        trends.reverse()
        
        return {
            "trends": trends,
            "period": f"Last {days} days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in trends", exc_info=True)
        raise HTTPException(status_code=500, detail=get_safe_error_message(e, "trends"))


@app.get("/api/categories")
def get_categories():
    """Get spending breakdown by category (current month)"""
    try:
        records = get_sheet_data()
        
        # Get current month
        now = datetime.now(tz=WIB)
        current_month = now.month
        current_year = now.year
        
        categories = {}
        
        for record in records:
            # Parse date
            date_str = record.get('Tanggal', '')
            if not date_str:
                continue
                
            try:
                day, month, year = map(int, date_str.split('/'))
                trans_date = datetime(year, month, day)
                
                # Filter current month and pengeluaran only
                if (trans_date.month == current_month and 
                    trans_date.year == current_year and 
                    record.get('Tipe') == 'Pengeluaran'):
                    
                    kategori = record.get('Kategori', 'Lainnya')
                    jumlah = abs(float(record.get('Jumlah', 0)))
                    
                    if kategori not in categories:
                        categories[kategori] = 0
                    
                    categories[kategori] += jumlah
                    
            except:
                continue
        
        # Convert to list format for frontend
        category_list = [
            {"name": k, "value": v} 
            for k, v in categories.items()
        ]
        
        # Sort by value descending
        category_list.sort(key=lambda x: x['value'], reverse=True)
        
        return {
            "categories": category_list,
            "total": sum(c['value'] for c in category_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monthly-comparison")
def get_monthly_comparison(months: int = 3):
    """Get monthly income vs expense comparison"""
    try:
        records = get_sheet_data()
        
        monthly_data = {}
        
        for record in records:
            date_str = record.get('Tanggal', '')
            if not date_str:
                continue
                
            try:
                day, month, year = map(int, date_str.split('/'))
                month_key = f"{year}-{month:02d}"
                month_name = datetime(year, month, 1).strftime('%b %Y')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "month": month_name,
                        "pemasukan": 0,
                        "pengeluaran": 0
                    }
                
                tipe = record.get('Tipe', '')
                jumlah = float(record.get('Jumlah', 0))
                
                if tipe == 'Pemasukan':
                    monthly_data[month_key]["pemasukan"] += jumlah
                elif tipe == 'Pengeluaran':
                    monthly_data[month_key]["pengeluaran"] += abs(jumlah)
                    
            except:
                continue
        
        # Get last N months
        comparison = list(monthly_data.values())[-months:]
        
        return {
            "comparison": comparison,
            "period": f"Last {months} months"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/pdf")
def export_pdf(preset: str = 'this_month', start: str = None, end: str = None):
    """Export transaksi ke PDF berdasarkan preset atau rentang tanggal"""
    try:
        records = get_sheet_data()

        today = date.today()
        period_label = ''

        if preset == 'all':
            filtered = records
            period_label = 'Semua data'
        elif preset == 'last_month':
            first_day = date(today.year, today.month, 1) - timedelta(days=1)
            start_date = date(first_day.year, first_day.month, 1)
            end_date = date(first_day.year, first_day.month, first_day.day)
            filtered = filter_records_by_range(records, start_date, end_date)
            period_label = f"{start_date.strftime('%B %Y')}"
        elif preset == 'custom':
            if not start or not end:
                raise HTTPException(status_code=400, detail="start dan end wajib untuk preset custom")
            start_date = datetime.strptime(start, '%Y-%m-%d').date()
            end_date = datetime.strptime(end, '%Y-%m-%d').date()
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="start tidak boleh lebih besar dari end")
            filtered = filter_records_by_range(records, start_date, end_date)
            period_label = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        else:  # this_month default
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year, 12, 31)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
            filtered = filter_records_by_range(records, start_date, end_date)
            period_label = f"{today.strftime('%B %Y')}"

        pdf_buffer = build_pdf(filtered, period_label)

        headers = {
            "Content-Disposition": "attachment; filename=transaksi.pdf"
        }
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error export pdf: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(tz=WIB).isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)