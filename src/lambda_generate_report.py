import os
import boto3
import psycopg2
from bedrock_client import BedrockClient
from fpdf import FPDF
from datetime import datetime

# Environment variables: DB connection, S3 bucket
DB_HOST = os.environ['DB_HOST']
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASS = os.environ['DB_PASS']
S3_BUCKET = os.environ['REPORTS_BUCKET']

bedrock = BedrockClient()
s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Connect to DB
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute('SELECT * FROM transactions')
    transactions = cur.fetchall()
    # Prepare data for Bedrock
    tx_data = [dict(zip([desc[0] for desc in cur.description], row)) for row in transactions]
    # Generate report text
    report = bedrock.generate_insights({'transactions': tx_data})
    summary = report['summary']
    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Financial Report', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, summary)
    pdf_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(pdf_file)
    # Upload to S3
    s3.upload_file(pdf_file, S3_BUCKET, pdf_file, ExtraArgs={'ContentType': 'application/pdf'})
    s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{pdf_file}"
    # Save report metadata
    cur.execute('INSERT INTO reports (name, url, created_at) VALUES (%s, %s, %s)', (pdf_file, s3_url, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()
    return {'status': 'success', 'url': s3_url}
