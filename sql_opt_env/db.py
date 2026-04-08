import os
import json
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from sql_opt_env.query_bank import SCHEMA_DDL

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "openenv")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "sqlenv")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME, port=DB_PORT
    )


def setup_db():
    try:
        conn = get_connection()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(SCHEMA_DDL)

        # Insert some dummy data if empty
        cur.execute("SELECT count(*) FROM customer;")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO customer (c_custkey, c_name, c_address, c_nationkey, c_phone, c_acctbal, c_mktsegment, c_comment)
                SELECT i, 'Customer#' || i, 'Address ' || i, i % 25, '123-456-7890', 1000.00, 'SEGMENT', 'Comment'
                FROM generate_series(1, 1000) i;
            """)
            cur.execute("""
                INSERT INTO orders (o_orderkey, o_custkey, o_orderstatus, o_totalprice, o_orderdate, o_orderpriority, o_clerk, o_shippriority, o_comment)
                SELECT i, (i % 1000) + 1, 'O', 1500.00, CURRENT_DATE, '1-URGENT', 'Clerk', 0, 'Comment'
                FROM generate_series(1, 5000) i;
            """)
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to setup DB: {e}")


def hash_result_set(results):
    # Create a deterministic hash of the result set
    s = json.dumps(results, default=str, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def execute_query_metrics(sql):
    """Executes SQL and returns (execution_time_ms, plan_json, result_hash, error_str)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Get EXPLAIN ANALYZE
        cur.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}")
        explain_plan = cur.fetchone()[0][0]
        execution_time_ms = explain_plan.get("Execution Time", 0.0)

        # 2. Get actual results to hash for semantic correctness
        cur.execute(sql)
        results = cur.fetchall()
        # Convert RealDictRow to standard dict for hashing
        results_list = [dict(r) for r in results]
        result_hash = hash_result_set(results_list)

        return execution_time_ms, explain_plan, result_hash, None
    except Exception as e:
        return 0.0, None, None, str(e)
    finally:
        if conn:
            conn.close()
