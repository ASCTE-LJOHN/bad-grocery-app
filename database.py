# database.py
import psycopg2
from configparser import ConfigParser
from models import Product

class DatabaseManager:
    def __init__(self, config_file='config.ini'):
        self.config = ConfigParser()
        self.config.read(config_file)
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.config['database']['host'],
                dbname=self.config['database']['dbname'],
                user=self.config['database']['user'],
                password=self.config['database']['password']
            )
            print("Database connected successfully")
        except Exception as e:
            print(f"Error connecting to database: {e}")

    def create_table(self):
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        price DECIMAL(10, 2) NOT NULL,
                        category VARCHAR(255)
                    );
                """)
                self.conn.commit()

    def insert_product(self, product):
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO products (name, price, category)
                    VALUES (%s, %s, %s) RETURNING id;
                """, (product.name, product.price, product.category))
                product.id = cur.fetchone()[0]
                self.conn.commit()
                return product

    def search_products(self, query):
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, price, category FROM products
                    WHERE name ILIKE %s OR category ILIKE %s;
                """, (f'%{query}%', f'%{query}%'))
                rows = cur.fetchall()
                return [Product(id=row[0], name=row[1], price=row[2], category=row[3]) for row in rows]

    def close(self):
        if self.conn:
            self.conn.close()