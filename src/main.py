import os
import sys
# DON\'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_cors import CORS
from src.models.user import db, User
from src.models.product import Product, Category
from src.models.order import Order, OrderItem, CartItem
from src.routes.user import user_bp

# Get the absolute path to the directory containing main.py (which is src/)
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(basedir, '..', 'static'), # Corrected path for static
    template_folder=os.path.join(basedir, '..', 'templates') # This was already correct
)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

app.register_blueprint(user_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables and sample data
with app.app_context():
    db.create_all()
    
    # Create sample categories if they don\'t exist
    if Category.query.count() == 0:
        categories = [
            Category(name='Pizza', description='Delicious pizzas with various toppings'),
            Category(name='Burgers', description='Juicy burgers with fresh ingredients'),
            Category(name='Pasta', description='Italian pasta dishes'),
            Category(name='Desserts', description='Sweet treats and desserts'),
            Category(name='Beverages', description='Refreshing drinks and beverages')
        ]
        for category in categories:
            db.session.add(category)
        db.session.commit()
    
    # Create sample products if they don\'t exist
    if Product.query.count() == 0:
        products = [
            Product(name='Margherita Pizza', description='Classic pizza with tomato sauce, mozzarella, and basil', 
                   price=12.99, category_id=1, image_url='/static/images/margherita-pizza.jpg'),
            Product(name='Pepperoni Pizza', description='Pizza with pepperoni, mozzarella, and tomato sauce', 
                   price=14.99, category_id=1, image_url='/static/images/pepperoni-pizza.jpg'),
            Product(name='Classic Burger', description='Beef patty with lettuce, tomato, onion, and special sauce', 
                   price=9.99, category_id=2, image_url='/static/images/classic-burger.jpg'),
            Product(name='Chicken Burger', description='Grilled chicken breast with fresh vegetables', 
                   price=10.99, category_id=2, image_url='/static/images/chicken-burger.jpg'),
            Product(name='Spaghetti Carbonara', description='Creamy pasta with bacon and parmesan cheese', 
                   price=13.99, category_id=3, image_url='/static/images/carbonara.jpg'),
            Product(name='Chocolate Cake', description='Rich chocolate cake with chocolate frosting', 
                   price=6.99, category_id=4, image_url='/static/images/chocolate-cake.jpg'),
            Product(name='Coca Cola', description='Refreshing cola drink', 
                   price=2.99, category_id=5, image_url='/static/images/coca-cola.jpg')
        ]
        for product in products:
            db.session.add(product)
        db.session.commit()
    
    # Create admin user if it doesn\'t exist
    if not User.query.filter_by(is_admin=True).first():
        admin = User(username='admin', email='admin@fooddelivery.com', 
                    first_name='Admin', last_name='User', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

# Main routes
@app.route('/')
def home():
    categories = Category.query.all()
    featured_products = Product.query.filter_by(is_available=True).limit(6).all()
    return render_template('home.html', categories=categories, featured_products=featured_products)

@app.route("/products")
@app.route("/products/<int:category_id>")
def products(category_id=None):
    categories = Category.query.all()
    
    if category_id:
        products_query = Product.query.filter_by(category_id=category_id, is_available=True)
        current_category = Category.query.get(category_id)
    else:
        products_query = Product.query.filter_by(is_available=True)
        current_category = None
    
    products = products_query.order_by(Product.name).all()

    cart_count = 0
    if "user_id" in session:
        user_id = session["user_id"]
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        cart_count = sum(item.quantity for item in cart_items)

    return render_template(
        "product.html",
        products=products,
        categories=categories,
        current_category=current_category,
        cart_count=cart_count
    )

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login to view your cart', 'warning')
        return redirect(url_for('login'))
    
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/about')
def about():
    return render_template('about_us.html')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        flash('Please login to access admin dashboard', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    products = Product.query.all()
    orders = Order.query.all()
    categories = Category.query.all()
    
    # Calculate statistics
    total_revenue = sum(order.total_amount for order in orders)
    total_orders = len(orders)
    total_products = len(products)
    
    return render_template('admin_dashboard.html', 
                         products=products, orders=orders, categories=categories,
                         total_revenue=total_revenue, total_orders=total_orders, 
                         total_products=total_products)

# API routes for AJAX functionality
@app.route('/api/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    # Check if item already in cart
    existing_item = CartItem.query.filter_by(user_id=session['user_id'], product_id=product_id).first()
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=session['user_id'], product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Item added to cart'})

@app.route('/api/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    
    cart_item = CartItem.query.filter_by(id=item_id, user_id=session['user_id']).first()
    
    if cart_item:
        if quantity > 0:
            cart_item.quantity = quantity
        else:
            db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Item not found'})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        return jsonify({'success': True, 'message': 'Login successful', 'is_admin': user.is_admin})
    
    return jsonify({'success': False, 'message': 'Invalid username or password'})

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'})
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already exists'})
    
    # Create new user
    user = User(username=username, email=email, first_name=first_name, last_name=last_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Registration successful'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


