# Archive - Unused Legacy Files

This directory contains old files that are no longer used in the production system but are kept for reference.

## Files:

- **lambda_function.py** - Old DynamoDB-based Lambda handler (replaced by handlers.py with PostgreSQL)
- **summary_handler.py** - Old DynamoDB-based summary handler (replaced by handlers.summary_handler with PostgreSQL)

## Why These Were Replaced:

The original system was designed to use DynamoDB, but the final architecture uses PostgreSQL with a comprehensive relational schema. These files were replaced with the modular handlers.py that properly integrates with the database schema in database.sql.

## Current Production System:

- **handlers.py** - Contains all Lambda handlers with PostgreSQL integration
- **db.py** - Database operations for PostgreSQL
- **parsers.py** - Receipt parsing utilities
- **bedrock_client.py** - AI classification using AWS Bedrock

Date archived: September 20, 2025