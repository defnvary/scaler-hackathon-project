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
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(o_orderstatus);
"""

QUERIES = {
    "easy": [
        {
            "name": "wide_table_scan",
            "description": "SELECT * on wide table. Task: Select only necessary columns.",
            "sql": "SELECT * FROM orders WHERE o_orderstatus = 'O' LIMIT 100;",
        },
        {
            "name": "redundant_distinct",
            "description": "Unnecessary DISTINCT on a PRIMARY KEY column. Task: Remove DISTINCT.",
            "sql": "SELECT DISTINCT o_orderkey, o_custkey FROM orders WHERE o_totalprice > 1000;",
        },
    ],
    "medium": [
        {
            "name": "implicit_join",
            "description": "Legacy implicit cross-join syntax. Task: Convert to explicit INNER JOIN.",
            "sql": "SELECT c.c_name, o.o_totalprice FROM customer c, orders o WHERE c.c_custkey = o.o_custkey AND o.o_orderstatus = 'F';",
        },
        {
            "name": "union_all_optimization",
            "description": "Using UNION where UNION ALL is sufficient (no overlap possible). Task: Use UNION ALL.",
            "sql": "SELECT c_name FROM customer WHERE c_nationkey = 1 UNION SELECT c_name FROM customer WHERE c_nationkey = 2;",
        },
    ],
    "hard": [
        {
            "name": "n_plus_one_correlated",
            "description": "Correlated subquery in SELECT clause causing N+1. Task: Flatten into a LEFT JOIN + GROUP BY.",
            "sql": "SELECT c.c_name, (SELECT COUNT(*) FROM orders o WHERE o.o_custkey = c.c_custkey AND o.o_totalprice > 2000) as high_value_count FROM customer c;",
        }
    ],
}


class QueryBank:
    def __init__(self):
        self.schema = SCHEMA_DDL
        self.queries = QUERIES

    def sample(self, difficulty=None):
        if not difficulty or difficulty not in self.queries:
            # Randomly pick difficulty
            difficulty = random.choice(["easy", "medium", "hard"])

        task = random.choice(self.queries[difficulty])
        return task["sql"].strip(), self.schema, difficulty


query_bank = QueryBank()
