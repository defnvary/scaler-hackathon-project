import random

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS customer (
    c_custkey       INTEGER PRIMARY KEY,
    c_name          VARCHAR(25) NOT NULL,
    c_address       VARCHAR(40) NOT NULL,
    c_nationkey     INTEGER NOT NULL,
    c_phone         CHAR(15) NOT NULL,
    c_acctbal       DECIMAL(15,2)   NOT NULL,
    c_mktsegment    CHAR(10) NOT NULL,
    c_comment       VARCHAR(117) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    o_orderkey      INTEGER PRIMARY KEY,
    o_custkey       INTEGER NOT NULL,
    o_orderstatus   CHAR(1) NOT NULL,
    o_totalprice    DECIMAL(15,2) NOT NULL,
    o_orderdate     DATE NOT NULL,
    o_orderpriority CHAR(15) NOT NULL,
    o_clerk         CHAR(15) NOT NULL,
    o_shippriority  INTEGER NOT NULL,
    o_comment       VARCHAR(79) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_custkey ON orders(o_custkey);
"""

QUERIES = {
    "easy": [
        {
            "description": "SELECT * on wide table (Easy)",
            "sql": "SELECT * FROM orders WHERE o_orderstatus = 'O';",
            "optimal_hint": "Select only necessary columns.",
        }
    ],
    "medium": [
        {
            "description": "Implicit Cross Join (Medium)",
            "sql": "SELECT DISTINCT c.c_name, o.o_totalprice FROM customer c, orders o WHERE c.c_custkey = o.o_custkey AND o.o_orderstatus = 'O';",
            "optimal_hint": "Use explicit INNER JOIN and remove DISTINCT if 1-to-many is intended.",
        }
    ],
    "hard": [
        {
            "description": "Correlated Subquery (Hard)",
            "sql": "SELECT c.c_name, (SELECT COUNT(*) FROM orders o WHERE o.o_custkey = c.c_custkey AND o.o_totalprice > 1000) as high_value_orders FROM customer c;",
            "optimal_hint": "Flatten into a LEFT JOIN with GROUP BY to avoid N+1.",
        }
    ],
}


class QueryBank:
    def __init__(self):
        self.schema = SCHEMA_DDL
        self.queries = QUERIES

    def sample(self, difficulty=None):
        if not difficulty or difficulty not in self.queries:
            difficulty = random.choice(["easy", "medium", "hard"])
        query = random.choice(self.queries[difficulty])
        return query["sql"].strip(), self.schema, difficulty


query_bank = QueryBank()
