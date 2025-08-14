from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'projeto_romerito'
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"

DB_FILE = 'banco.db'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()
    
    return conn

class User(UserMixin):
    def __init__(self, id, email, username):
        self.id = id
        self.email = email
        self.username = username

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT id, email, username FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['email'], user_data['username'])
    return None

produtos = {}

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        user_cart_key = f'cart_{current_user.id}'
        if user_cart_key not in session:
            session[user_cart_key] = []
    else:
        if 'cart' not in session:
            session['cart'] = []

@app.route('/')
def index():
    rendered_template = render_template('index.html')
    response = make_response(rendered_template)    
    response.headers['X-Custom-Header'] = 'Aorus Store'
    return response

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        flash('Você já está logado!', 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('user')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not username or not password or not confirm_password:
            flash('Todos os campos são obrigatórios.', 'danger')
            return render_template('cadastro.html', email=email)

        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('cadastro.html', email=email)
        
        conn = get_db_connection()
        user_existente = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user_existente:
            conn.close()
            flash('Este email já está cadastrado. Tente outro ou faça login.', 'danger')
            return render_template('cadastro.html', email=email)

        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', (username, email, hashed_password))
        conn.commit()
        conn.close()
        
        flash('Cadastro realizado com sucesso! Faça login agora.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('Você já está logado!', 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email_digitado = request.form.get('email')
        senha_digitada = request.form.get('password')
        
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE email = ?', (email_digitado,)).fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password_hash'], senha_digitada):
            user = User(user_data['id'], user_data['email'], user_data['username'])
            login_user(user)
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha inválidos.', 'danger')
            return render_template('login.html', email=email_digitado)
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user_cart_key = f'cart_{current_user.id}'
    if user_cart_key in session:
        session.pop(user_cart_key, None)
    logout_user()
    flash('Você foi desconectado(a).', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/categorias')
def categorias():
    return render_template('categorias.html')

@app.route('/categorias/futebol')
def futebol():
    return render_template('futebol.html', produtos=produtos)

@app.route('/categorias/basquete')
def basquete():
    return render_template('basquete.html', produtos=produtos)

@app.route('/categorias/volei')
def volei():
    return render_template('volei.html', produtos=produtos)

@app.route('/categorias/ciclismo')
def ciclismo():
    return render_template('ciclismo.html', produtos=produtos)

@app.route('/categorias/aqua')
def aqua():
    return render_template('aqua.html', produtos=produtos)

@app.route('/categorias/tacos')
def tacos():
    return render_template('tacos.html', produtos=produtos)

@app.route('/categorias/automobilismo')
def auto():
    return render_template('auto.html', produtos=produtos)

@app.route('/add_to_cart', methods=['POST'])
@login_required 
def add_to_cart():
    product_image = request.form.get('product_image')
    product_description = request.form.get('product_description')
    product_price = request.form.get('product_price') 

    if current_user.is_authenticated:
        user_cart_key = f'cart_{current_user.id}'
        cart = session.get(user_cart_key, [])
        if len(cart) >= 12:
            flash('Limite de 12 produtos no carrinho atingido.', 'warning')
        else:
            cart.append({'image': product_image, 'description': product_description, 'price': product_price})
            session[user_cart_key] = cart
            flash('Produto adicionado ao carrinho!', 'success')
    else:
        cart = session.get('cart', [])
        if len(cart) >= 12:
            flash('Limite de 12 produtos no carrinho atingido.', 'warning')
        else:
            cart.append({'image': product_image, 'description': product_description, 'price': product_price})
            session['cart'] = cart
            flash('Produto adicionado ao carrinho! Faça login para salvar seu carrinho.', 'success')

    return redirect(request.referrer or url_for('index'))

@app.route('/carrinho')
@login_required
def carrinho():
    if current_user.is_authenticated:
        user_cart_key = f'cart_{current_user.id}'
        cart_items = session.get(user_cart_key, [])
    else:
        cart_items = session.get('cart', [])
    return render_template('carrinho.html', cart_items=cart_items)

@app.route('/remove_from_cart/<int:item_index>', methods=['POST'])
@login_required
def remove_from_cart(item_index):
    if current_user.is_authenticated:
        user_cart_key = f'cart_{current_user.id}'
        cart = session.get(user_cart_key, [])
        if 0 <= item_index < len(cart):
            cart.pop(item_index)
            session[user_cart_key] = cart
            flash('Produto removido do carrinho.', 'success')
        else:
            flash('Erro ao remover o produto.', 'danger')
    else:
        cart = session.get('cart', [])
        if 0 <= item_index < len(cart):
            cart.pop(item_index)
            session['cart'] = cart
            flash('Produto removido do carrinho.', 'success')
        else:
            flash('Erro ao remover o produto.', 'danger')

    return redirect(url_for('carrinho'))

@app.route('/checkout', methods=['POST'])
def checkout():
    total_price = 0
    bought_products = []
    
    if current_user.is_authenticated:
        user_cart_key = f'cart_{current_user.id}'
        cart_items = session.get(user_cart_key, [])
        for item in cart_items:
            price_str = item['price'].replace('R$ ', '').replace(',', '.')
            total_price += float(price_str)
            bought_products.append(item)
        
        session.pop(user_cart_key, None)
    else:
        cart_items = session.get('cart', [])
        for item in cart_items:
            price_str = item['price'].replace('R$ ', '').replace(',', '.')
            total_price += float(price_str)
            bought_products.append(item)
            
        session.pop('cart', None)
        
    total_price_formatted = "R$ {:.2f}".format(total_price).replace('.', ',')
    
    return render_template('compra_finalizada.html', total_price=total_price_formatted, bought_products=bought_products)

if __name__ == '__main__':
    app.run(debug=True)

