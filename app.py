from functools import wraps
import sqlite3
from flask import Flask, Blueprint, flash, redirect, render_template, request, jsonify, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
import os

app = Flask(__name__)

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
Session(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120))

class Order(db.Model):
    oid = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email_adress = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(30), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    zip = db.Column(db.Integer, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # 'cash' or 'credit card'


class Product(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    brand = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(10), nullable=False)

class Productw(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    brand = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(10), nullable=False)


@app.route('/sentorder', methods=['POST'])
def sentorder():
    if request.method == 'POST':
        customer_name = request.form['name']
        phone_number = request.form['phone']
        email_adress = request.form['email']
        address = request.form['address']
        country = request.form['country']
        city = request.form['city']
        zip = request.form['zip']
        payment_type = request.form['paymentMethod']

        theorder = Order(
            customer_name=customer_name,
            phone_number=phone_number,
            email_adress=email_adress,
            address=address,
            country=country,
            city=city,
            zip=zip,
            payment_type=payment_type
        )

        db.session.add(theorder)
        db.session.commit()
        flash("Order sent")

@app.route('/add_product', methods=['POST'])
def add_product():
    if request.method == 'POST':
        code = request.form['code']
        brand = request.form['brand']
        name = request.form['name']
        image = request.form['image']
        price = float(request.form['price'])
        size = request.form['size'] 

        new_product = Product(code=code, brand=brand, name=name, image=image, price=price, size=size)
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!")

        # Redirect to a page displaying the updated list of products or to another appropriate location.
        return redirect(url_for('.products'))

@app.route('/add_product', methods=['GET'])
def render_add_product_form():
    return render_template('add_product.html')

@app.route('/add_productw', methods=['POST'])
def add_productw():
    if request.method == 'POST':
        code = request.form['code']
        brand = request.form['brand']
        name = request.form['name']
        image = request.form['image']
        price = float(request.form['price'])
        size = request.form['size'] 

        new_product = Productw(code=code, brand=brand, name=name, image=image, price=price, size=size)
        db.session.add(new_product)
        db.session.commit()
        flash("Product added successfully!")
        return redirect(url_for('.productsw'))

        # Redirect to a page displaying the updated list of products or to another appropriate location.

@app.route('/add_productw', methods=['GET'])
def render_add_product_formw():
    return render_template('add_productw.html')


@app.route('/men')
def products():
    try:
        products = Product.query.all()
        return render_template("men.html", products=products)
    except Exception as e:
        print(e)
        return "An error occurred while fetching data."

def array_merge(first_array, second_array):
    if isinstance(first_array, list) and isinstance(second_array, list):
        return first_array + second_array
    elif isinstance(first_array, dict) and isinstance(second_array, dict):
        return dict(list(first_array.items()) + list(second_array.items()))
    elif isinstance(first_array, set) and isinstance(second_array, set):
        return first_array.union(second_array)
    return False


@app.route('/add', methods=['POST'])
def add_product_to_cart():
    cursor = None
    try:
        _quantity = int(request.form['quantity'])
        _code = request.form['code']
        if _quantity and _code and request.method == 'POST':
            db_path = os.path.join(app.instance_path, 'users.db')
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM product WHERE code=?", (_code,))
                rows_product = cursor.fetchone()
                redirect_route = '.products'
                if not rows_product:
                    cursor.execute("SELECT * FROM productw WHERE code=?", (_code,))
                    rows_productw = cursor.fetchall()
                    redirect_route = '.productsw'

                    if not rows_productw:
                        return 'Product not found in both tables'
    
                    row = rows_productw[0]  # Assuming you want to use the first result from productw
                else:
                    row = rows_product

                if row is not None:
                    itemArray = {row[1]: {'name': row[3], 'code': row[1], 'quantity': _quantity, 'size': row[6], 'price': row[5], 'brand' : row[2], 'image': row[4], 'total_price': _quantity * row[5]}}
                else:
                    return 'Product not found'
                
                all_total_price = 0.0
                all_total_quantity = 0

                session.modified = True
                if 'cart_item' in session:
                    if row[0] in session['cart_item']:
                        for key, value in session['cart_item'].items():
                            if row[0] == key:
                                old_quantity = session['cart_item'][key]['quantity']
                                total_quantity = old_quantity + _quantity
                                session['cart_item'][key]['quantity'] = total_quantity
                                session['cart_item'][key]['total_price'] = total_quantity * row[5]
                    else:
                        session['cart_item'] = array_merge(session['cart_item'], itemArray)

                    
                    for key, value in session['cart_item'].items():
                        individual_quantity = int(session['cart_item'][key]['quantity'])
                        individual_price = float(session['cart_item'][key]['total_price'])
                        all_total_quantity = all_total_quantity + int(individual_quantity)
                        all_total_price = all_total_price + float(individual_price)

                else:
                    session['cart_item'] = itemArray
                    all_total_quantity = all_total_quantity + _quantity
                    all_total_price = all_total_price + _quantity * row[5]
                
                
                session['all_total_quantity'] = all_total_quantity
                session['all_total_price'] = all_total_price
            flash("The product has been added to cart!")
            return redirect(url_for(redirect_route))
        else:
            return 'Error while adding item to cart'
    except Exception as e:
        print(e)
    finally:
        cursor.close() 
        conn.close()


@app.route('/empty')
def empty_cart():
 try:
  session.clear()
  return redirect(url_for('.products'))
 except Exception as e:
  print(e)
 
@app.route('/delete/<string:code>')
def delete_product(code):
 try:
  all_total_price = 0
  all_total_quantity = 0
  session.modified = True
   
  for item in session['cart_item'].items():
   if item[0] == code:    
    session['cart_item'].pop(item[0], None)
    if 'cart_item' in session:
     for key, value in session['cart_item'].items():
      individual_quantity = int(session['cart_item'][key]['quantity'])
      individual_price = float(session['cart_item'][key]['total_price'])
      all_total_quantity = all_total_quantity + individual_quantity
      all_total_price = all_total_price + individual_price
    break
   
  if all_total_quantity == 0:
   del session['cart_item']
  else:
   session['all_total_quantity'] = all_total_quantity
   session['all_total_price'] = all_total_price
   
  return redirect(url_for('.cart'))
 except Exception as e:
  print(e)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        query = text("SELECT * FROM user WHERE username = :username")
        result = db.session.execute(query, {"username": request.form.get("username")}).fetchone()

        # Ensure username exists and password is correct
        if result is None or not check_password_hash(result[2], request.form.get("password")):  # Assuming password hash is at index 2
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = result[0]  # Assuming user ID is at index 0
        flash("You have been successfully logged in!")

        # Redirect user to home page
        session['logged_in'] = True
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)

        query = text("SELECT * FROM user WHERE username = :username")
        existing_user = db.session.execute(query, {"username": username}).fetchone()

        if existing_user:
            return apology("username already exists", 400)

        if not password:
            return apology("must provide password", 400)

        if password == confirmation:
            password_hash = generate_password_hash(password)

            query = text("INSERT INTO user (username, password_hash) VALUES (:username, :password_hash)")
            db.session.execute(query, {"username": username, "password_hash": password_hash})
            db.session.commit()
            flash("Registered!")

            return redirect("/")
        else:
            return apology("passwords do not match", 400)

    else:
        return render_template("register.html")


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/favorites")
def favorites():
    return render_template("favorites.html")

@app.route("/women")
def productsw():
    try:
        products = Productw.query.all()
        return render_template("women.html", products=products)
    except Exception as e:
        print(e)
        return "An error occurred while fetching data."

@app.route("/kids")
def kids():
    return render_template("kids.html")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.route("/order-sent")
def ordersent():
   try:
      del session['cart_item']
      return render_template("order-sent.html")
   except Exception as e:
      print(e)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8001)