from flask import Flask, render_template, request, jsonify
import xml.etree.ElementTree as ET
from database import DatabaseManager
from models import Product

app = Flask(__name__)

# Load theme from XML
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
    except Exception as e:
        print(f"Error loading config.xml: {e}. Using defaults.")
        return {
            'bg': '#f8f9fa',
            'text': '#212529',
            'accent': '#0d6efd',
            'btn_bg': '#0d6efd',
            'btn_text': '#ffffff',
            'container': '#ffffff',
            'border': '#dee2e6',
            'font': 'system-ui, -apple-system, sans-serif',
        }

theme = load_theme()

# Database (you can keep config.ini or use XML or env vars)
# For this example we still use config.ini — but you can switch to XML if preferred
db_manager = DatabaseManager()  # reads config.ini by default

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
        db_manager.insert_product(product)
        return jsonify({'message': 'Product added', 'product': product.to_dict()})
    
    return render_template('import.html', theme=theme)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        products = db_manager.search_products(query)
        return jsonify({'products': [p.to_dict() for p in products]})
    
    return render_template('search.html', theme=theme)

if __name__ == '__main__':
    print("Theme loaded:", theme)
    app.run(debug=True)