import psycopg2
import psycopg2.extras
import os
import logging
import uuid
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_conn():
    """Get PostgreSQL connection with environment variables"""
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ.get('DB_PORT', '5432'),
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        connect_timeout=5,
        cursor_factory=psycopg2.extras.RealDictCursor
    )

@contextmanager
def get_db_cursor():
    """Context manager for database operations"""
    conn = None
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                yield cur
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def upsert_vendor(cur, org_id: str, vendor_name: str) -> str:
    """Upsert vendor and return vendor_id"""
    if not vendor_name or len(vendor_name.strip()) == 0:
        return None
    
    vendor_name = vendor_name.strip()[:100]  # Clamp length
    
    # Try to get existing vendor
    cur.execute("""
        SELECT id FROM vendors 
        WHERE organization_id = %s AND name = %s
    """, (org_id, vendor_name))
    
    result = cur.fetchone()
    if result:
        return result['id']
    
    # Insert new vendor (no unique constraint, so we just insert)
    vendor_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO vendors (id, organization_id, name, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
        RETURNING id
    """, (vendor_id, org_id, vendor_name))
    
    result = cur.fetchone()
    return result['id']

def get_or_create_category(cur, org_id: str, category_name: str) -> str:
    """Get or create category and return category_id"""
    if not category_name:
        category_name = "Others"
    
    category_name = category_name.strip()[:100]  # Clamp length
    
    # Try to get existing category
    cur.execute("""
        SELECT id FROM categories 
        WHERE organization_id = %s AND name = %s
    """, (org_id, category_name))
    
    result = cur.fetchone()
    if result:
        return result['id']
    
    # Insert new category (remove ON CONFLICT since constraint may not exist)
    category_id = str(uuid.uuid4())
    try:
        cur.execute("""
            INSERT INTO categories (id, organization_id, name, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            RETURNING id
        """, (category_id, org_id, category_name))
    except Exception as e:
        # If insert fails due to duplicate, try to find existing category
        logger.warning(f"Category insert failed: {str(e)}, trying to find existing")
        cur.execute("""
            SELECT id FROM categories 
            WHERE organization_id = %s AND name = %s
        """, (org_id, category_name))
        result = cur.fetchone()
        if result:
            return result['id']
        # If still not found, generate new ID and try without conflict handling
        category_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO categories (id, organization_id, name, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            RETURNING id
        """, (category_id, org_id, category_name))
    
    result = cur.fetchone()
    return result['id'] if result else category_id

def ensure_system_user_exists(cur, org_id: str) -> str:
    """Ensure a system user exists and return its ID - guaranteed to never return None"""
    # Use a predictable system user ID - but make it a valid UUID format
    system_user_id = "11111111-1111-1111-1111-" + org_id[:12].replace('-', '0')
    
    try:
        # Check if system user already exists
        cur.execute("SELECT id FROM users WHERE id = %s", (system_user_id,))
        result = cur.fetchone()
        if result:
            return system_user_id
    except Exception:
        pass
    
    # Create the system user with password (required field)
    try:
        # Import hash_password from handlers to create a proper hashed password
        import hashlib
        hashed_password = hashlib.sha256('system_password'.encode()).hexdigest()
        
        cur.execute("""
            INSERT INTO users (id, name, email, organization_id, password, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """, (system_user_id, 'System User', f'system@org.local', org_id, hashed_password))
        logger.info(f"Created system user with ID: {system_user_id}")
        return system_user_id
    except Exception as e:
        logger.error(f"Failed to create system user: {str(e)}")
        pass
    
    # Try to find any existing user from the org
    try:
        cur.execute("SELECT id FROM users WHERE organization_id = %s LIMIT 1", (org_id,))
        result = cur.fetchone()
        if result:
            return result['id']
    except Exception:
        pass
    
    # Absolute fallback - return a hardcoded UUID
    # This will likely cause a foreign key error, but it's better than null
    return "00000000-0000-0000-0000-000000000001"

def insert_document(cur, org_id: str, name: str, document_url: str, doc_type: str = 'receipt', uploaded_by: str = None) -> str:
    """Insert document and return document_id"""
    document_id = str(uuid.uuid4())
    
    # Use provided user_id or fallback to system user
    user_id = uploaded_by
    if not user_id:
        user_id = ensure_system_user_exists(cur, org_id)
    
    # Extra safety check
    if not user_id:
        user_id = "00000000-0000-0000-0000-000000000001"
    
    cur.execute("""
        INSERT INTO documents (id, organization_id, name, document_url, type, uploaded_by, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING id
    """, (document_id, org_id, name[:255], document_url, doc_type, user_id))
    
    result = cur.fetchone()
    return result['id']

def insert_ocr_result(cur, org_id: str, document_id: str, vendor_id: Optional[str], 
                     text: str, total_amount: float, currency: str, 
                     invoice_date: Optional[str], invoice_number: Optional[str], 
                     uploaded_by: str = None) -> str:
    """Insert OCR result and return ocr_result_id"""
    ocr_result_id = str(uuid.uuid4())
    
    # Clamp text field
    text = text[:3500] if text else ""
    invoice_number = invoice_number[:100] if invoice_number else None
    
    # Use provided user_id or fallback to system user
    user_id = uploaded_by
    if not user_id:
        user_id = ensure_system_user_exists(cur, org_id)
    
    cur.execute("""
        INSERT INTO ocr_results (
            id, organization_id, document_id, vendor_id, results, total_amount, 
            currency, invoice_date, invoice_number, uploaded_by, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING id
    """, (ocr_result_id, org_id, document_id, vendor_id, text, total_amount, 
          currency, invoice_date, invoice_number, user_id))
    
    result = cur.fetchone()
    return result['id']

def insert_transaction(cur, org_id: str, ocr_result_id: str, 
                      vendor_id: Optional[str], account_id: Optional[str], 
                      category_id: str, description: str, amount: float, 
                      currency: str, invoice_date: Optional[str], 
                      tx_type: str = 'expense') -> str:
    """Insert transaction and return transaction_id"""
    transaction_id = str(uuid.uuid4())
    
    description = description[:255] if description else ""
    
    cur.execute("""
        INSERT INTO transactions (
            id, organization_id, ocr_result_id, vendor_id, 
            account_id, category_id, description, amount, currency, 
            invoice_date, type, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING id
    """, (transaction_id, org_id, ocr_result_id, vendor_id, 
          account_id, category_id, description, amount, currency, 
          invoice_date, tx_type))
    
    result = cur.fetchone()
    return result['id']

def get_transactions_with_filters(cur, org_id: str, limit: int = 50, offset: int = 0,
                                from_date: Optional[str] = None, to_date: Optional[str] = None,
                                category: Optional[str] = None, vendor: Optional[str] = None) -> Tuple[List[Dict], int]:
    """Get transactions with JOIN and filters, plus total count"""
    
    # Base query with JOINs
    where_conditions = ["t.organization_id = %s"]
    params = [org_id]
    
    if from_date:
        where_conditions.append("COALESCE(t.invoice_date, t.created_at::date) >= %s")
        params.append(from_date)
    
    if to_date:
        where_conditions.append("COALESCE(t.invoice_date, t.created_at::date) <= %s")
        params.append(to_date)
    
    if category:
        where_conditions.append("c.name ILIKE %s")
        params.append(f"%{category}%")
    
    if vendor:
        where_conditions.append("v.name ILIKE %s")
        params.append(f"%{vendor}%")
    
    where_clause = " AND ".join(where_conditions)
    
    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM transactions t
        LEFT JOIN vendors v ON v.id = t.vendor_id
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE {where_clause}
    """
    
    cur.execute(count_query, params)
    total = cur.fetchone()['total']
    
    # Get paginated results
    results_query = f"""
        SELECT 
            t.id,
            COALESCE(t.invoice_date, t.created_at::date) as invoice_date,
            t.amount,
            t.currency,
            v.name as vendor_name,
            c.name as category_name,
            NULL as document_url,
            t.description,
            t.type
        FROM transactions t
        LEFT JOIN vendors v ON v.id = t.vendor_id
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE {where_clause}
        ORDER BY COALESCE(t.invoice_date, t.created_at) DESC
        LIMIT %s OFFSET %s
    """
    
    params.extend([limit, offset])
    cur.execute(results_query, params)
    
    items = []
    for row in cur.fetchall():
        items.append({
            'id': row['id'],
            'invoice_date': row['invoice_date'].isoformat() if row['invoice_date'] else None,
            'amount': float(row['amount']) if row['amount'] else 0.0,
            'currency': row['currency'],
            'vendor_name': row['vendor_name'],
            'category_name': row['category_name'],
            'document_url': row['document_url'],
            'description': row['description'],
            'type': row['type']
        })
    
    return items, total

def get_summary_data(cur, org_id: str) -> Dict[str, Any]:
    """Get KPIs and category breakdown"""
    
    # Get KPIs
    cur.execute("""
        SELECT 
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
            COUNT(*) as receipt_count,
            AVG(amount) as avg_per_receipt
        FROM transactions 
        WHERE organization_id = %s
    """, (org_id,))
    
    kpi_result = cur.fetchone()
    
    # Get top category
    cur.execute("""
        SELECT c.name, SUM(t.amount) as total
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.organization_id = %s AND t.type = 'expense'
        GROUP BY c.name
        ORDER BY total DESC
        LIMIT 1
    """, (org_id,))
    
    top_category_result = cur.fetchone()
    
    # Get spending by category (last 90 days)
    cur.execute("""
        SELECT 
            COALESCE(c.name, 'Uncategorized') as category,
            SUM(t.amount) as total
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.organization_id = %s 
            AND t.type = 'expense'
            AND COALESCE(t.invoice_date, t.created_at::date) >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY c.name
        ORDER BY total DESC
    """, (org_id,))
    
    category_results = cur.fetchall()
    
    kpis = {
        'total_expense': float(kpi_result['total_expense']) if kpi_result['total_expense'] else 0.0,
        'receipt_count': int(kpi_result['receipt_count']) if kpi_result['receipt_count'] else 0,
        'avg_per_receipt': float(kpi_result['avg_per_receipt']) if kpi_result['avg_per_receipt'] else 0.0,
        'top_category': {
            'name': top_category_result['name'] if top_category_result and top_category_result['name'] else 'None',
            'total': float(top_category_result['total']) if top_category_result and top_category_result['total'] else 0.0
        }
    }
    
    by_category_90d = []
    for row in category_results:
        by_category_90d.append({
            'category': row['category'],
            'total': float(row['total']) if row['total'] else 0.0
        })
    
    return {
        'kpis': kpis,
        'by_category_90d': by_category_90d
    }

def get_monthly_report(cur, org_id: str, year: int) -> List[Dict]:
    """Get monthly report by category"""
    cur.execute("""
        SELECT
            DATE_TRUNC('month', COALESCE(t.invoice_date, t.created_at)) AS month,
            COALESCE(c.name, 'Uncategorized') AS category,
            SUM(t.amount) AS total
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.organization_id = %s 
            AND DATE_PART('year', COALESCE(t.invoice_date, t.created_at)) = %s
        GROUP BY 1, 2
        ORDER BY 1, 2
    """, (org_id, year))
    
    results = []
    for row in cur.fetchall():
        results.append({
            'month': row['month'].isoformat() if row['month'] else None,
            'category': row['category'],
            'total': float(row['total']) if row['total'] else 0.0
        })
    
    return results

def get_forecast_data(cur, org_id: str) -> List[Dict]:
    """Get weekly cash flow data for forecasting"""
    cur.execute("""
        SELECT
            DATE_TRUNC('week', COALESCE(invoice_date, created_at)) AS week,
            SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS inflow,
            SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS outflow,
            SUM(CASE WHEN type='income' THEN amount ELSE -amount END) AS net
        FROM transactions
        WHERE organization_id = %s
        GROUP BY 1
        ORDER BY 1
    """, (org_id,))
    
    results = []
    for row in cur.fetchall():
        results.append({
            'week': row['week'].isoformat() if row['week'] else None,
            'inflow': float(row['inflow']) if row['inflow'] else 0.0,
            'outflow': float(row['outflow']) if row['outflow'] else 0.0,
            'net': float(row['net']) if row['net'] else 0.0
        })
    
    return results

def save_forecast(cur, org_id: str, horizon: int, granularity: str, series: List[Dict]) -> str:
    """Save forecast results to database"""
    forecast_id = str(uuid.uuid4())
    
    cur.execute("""
        INSERT INTO forecasts (id, organization_id, horizon, granularity, series, computed_at, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), NOW())
        RETURNING id
    """, (forecast_id, org_id, horizon, granularity, series))
    
    result = cur.fetchone()
    return result['id']

def get_latest_forecast(cur, org_id: str, max_age_hours: int = 24) -> Optional[Dict]:
    """Get latest forecast if not too old"""
    cur.execute("""
        SELECT series, computed_at
        FROM forecasts
        WHERE organization_id = %s 
            AND computed_at > NOW() - INTERVAL '%s hours'
        ORDER BY computed_at DESC
        LIMIT 1
    """, (org_id, max_age_hours))
    
    result = cur.fetchone()
    if result:
        return {
            'series': result['series'],
            'computed_at': result['computed_at']
        }
    return None
