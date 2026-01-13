from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import csv
from io import StringIO
import xml.etree.ElementTree as ET
from database import DatabaseManager
from contextlib import contextmanager
from models import Product
import sqlite3

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-flash-messages'  # required for flash

# Load theme from XML (unchanged)
def load_theme():
    try:
        tree = ET.parse('config.xml')
        root = tree.getroot()
        theme = root.find('theme')
        return {
            'bg': theme.find('background_color').text,
            'text': theme.find('text_color').text,
            'accent': theme.find('accent_color').text,
            'btn_bg': theme.find('button_bg').text,
            'btn_text': theme.find('button_text').text,
            'container': theme.find('container_bg').text,
            'border': theme.find('border_color').text,
            'font': theme.find('font_family').text,
        }
    except:
        return {
            'bg': '#f8f9fa',
            'text': '#212529',
            'accent': '#0d6efd',
            'btn_bg': '#0d6efd',
            'btn_text': '#ffffff',
            'container': '#ffffff',
            'border': '#dee2e6',
            'font': 'system-ui, sans-serif',
        }

theme = load_theme()

# Use SQLite — no config.ini needed anymore
# db_manager = DatabaseManager(db_file='grocery.db')
# Instead, create a context manager for per-request connections
@contextmanager
def get_db(db_file='grocery.db'):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Helper to get a cursor with context
def get_cursor():
    return get_db().__enter__().cursor()  # but we'll use conn directly in most cases


@app.route('/')
def index():
    return render_template('index.html', theme=theme)

@app.route('/import', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        category = request.form.get('category', '')
        product = Product(name=name, price=price, category=category)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (name, price, category)
                VALUES (?, ?, ?)
            """, (product.name, product.price, product.category))
            product.id = cursor.lastrowid
            conn.commit()

        return jsonify({'message': 'Product added', 'product': product.to_dict()})

    return render_template('import.html', theme=theme)

@app.route('/import-file', methods=['GET', 'POST'])
def import_file():
    if request.method == 'POST':
        # ... file handling remains the same ...
        if file and file.filename.lower().endswith('.csv'):
            try:
                stream = StringIO(file.stream.read().decode('utf-8'), newline='')
                csv_reader = csv.DictReader(stream)
                products = [dict(row) for row in csv_reader]

                success = 0
                failed = 0
                errors = []

                with get_db() as conn:
                    for prod in products:
                        try:
                            name = prod['name'].strip()
                            price = float(prod['price'])
                            category = prod.get('category', '').strip() or None
                            if not name:
                                raise ValueError("Missing name")

                            conn.execute("""
                                INSERT OR IGNORE INTO products (name, price, category)
                                VALUES (?, ?, ?)
                            """, (name, price, category))
                            success += 1
                        except Exception as e:
                            failed += 1
                            errors.append(f"Row error: {prod} → {str(e)}")
                    conn.commit()

                # ... flash message logic remains the same ...
                message = f"Import complete: {success} added"
                if failed:
                    message += f", {failed} failed"
                    if errors:
                        message += "<br><br>Errors:<br>" + "<br>".join(errors[:10])
                        if len(errors) > 10:
                            message += f"<br>... and {len(errors)-10} more"
                flash(message, 'success' if success > 0 else 'error')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
                return redirect(request.url)
        # ... rest unchanged ...
    return render_template('import_file.html', theme=theme)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        products = []

        with get_db() as conn:
            cursor = conn.execute("""
                SELECT id, name, price, category FROM products
                WHERE name LIKE ? OR category LIKE ?
            """, (f'%{query}%', f'%{query}%'))
            rows = cursor.fetchall()
            products = [Product(
                id=row['id'],
                name=row['name'],
                price=row['price'],
                category=row['category']
            ) for row in rows]

        return jsonify({'products': [p.to_dict() for p in products]})

    return render_template('search.html', theme=theme)

if __name__ == '__main__':
    print("Theme loaded:", theme)
    print("Using SQLite database: grocery.db")
    app.run(debug=True)