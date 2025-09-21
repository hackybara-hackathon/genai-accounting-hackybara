import psycopg2
import psycopg2.extras
import os
import bcrypt
import uuid
from contextlib import contextmanager

def get_conn():
    """Get PostgreSQL connection with environment variables"""
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ.get('DB_PORT', '5432'),
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        connect_timeout=10,
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
        print(f"Database error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_database_handler(event, context):
    """Initialize database with required schema and test data"""
    
    try:
        with get_db_cursor() as cur:
            print("Initializing database...")
            
            # Check if password column exists in users table
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'password'
            """)
            
            if not cur.fetchone():
                print("Adding password column to users table...")
                cur.execute("ALTER TABLE users ADD COLUMN password VARCHAR(255)")
            
            # Check if organizations table exists
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'organizations'
            """)
            
            if not cur.fetchone():
                print("Creating organizations table...")
                cur.execute("""
                    CREATE TABLE organizations (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # Create default organization if not exists
            org_id = os.environ.get('ORG_ID', '94fbdf4e-0e94-404a-9abb-76a20e22c855')
            cur.execute("SELECT id FROM organizations WHERE id = %s", (org_id,))
            if not cur.fetchone():
                print("Creating default organization...")
                cur.execute("""
                    INSERT INTO organizations (id, name) 
                    VALUES (%s, 'Hackybara Demo Organization')
                """, (org_id,))
            
            # Create test users if they don't exist
            test_users = [
                {
                    'name': 'Demo User',
                    'email': 'demo@example.com',
                    'password': 'password123'
                },
                {
                    'name': 'Test User', 
                    'email': 'test@example.com',
                    'password': 'password123'
                }
            ]
            
            for user_data in test_users:
                cur.execute("SELECT id FROM users WHERE email = %s", (user_data['email'],))
                if not cur.fetchone():
                    print(f"Creating user: {user_data['email']}")
                    user_id = str(uuid.uuid4())
                    hashed_password = hash_password(user_data['password'])
                    cur.execute("""
                        INSERT INTO users (id, name, email, organization_id, password)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, user_data['name'], user_data['email'], org_id, hashed_password))
            
            print("Database initialization completed successfully!")
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': '{"message": "Database initialized successfully"}'
            }
            
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': f'{{"error": "Database initialization failed: {str(e)}"}}'
        }