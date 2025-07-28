from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_forte_e_aleatoria_aqui'
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

usuarios_db = {}


class User(UserMixin):
    def __init__(self, user_id, email, username):
        self.id = user_id
        self.email = email
        self.username = username

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    if user_id in usuarios_db:
        user_data = usuarios_db[user_id]
        return User(user_data['id'], user_data['email'], user_data['username'])
    return None

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Inicializa o carrinho na sessão antes de cada requisição
@app.before_request
def before_request():
    # Se o usuário não estiver autenticado, não há necessidade de inicializar um carrinho específico de usuário
    if not current_user.is_authenticated:
        # Garante que um carrinho genérico vazio exista para usuários não logados, se necessário
        if 'cart' not in session:
            session['cart'] = []
        return

    # Para usuários autenticados, usa uma chave de sessão específica para o usuário
    user_cart_key = f'cart_{current_user.id}'
    if user_cart_key not in session:
        session[user_cart_key] = []


@app.route('/')
def index():
    return render_template('index.html')

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

        if email in usuarios_db:
            flash('Este email já está cadastrado. Tente outro ou faça login.', 'danger')
            return render_template('cadastro.html', email=email)

        hashed_password = generate_password_hash(password)
        usuarios_db[email] = {"password_hash": hashed_password, "id": email, "email": email, "username": username}
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

        if email_digitado in usuarios_db:
            user_data = usuarios_db[email_digitado]
            if check_password_hash(user_data['password_hash'], senha_digitada):
                user = User(user_data['id'], user_data['email'], user_data['username'])
                login_user(user)
                flash('Login bem-sucedido!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Email ou senha inválidos.', 'danger')
                return render_template('login.html', email=email_digitado)
        else:
            flash('Email ou senha inválidos.', 'danger')
            return render_template('login.html', email=email_digitado)

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Limpa o carrinho do usuário específico ao deslogar
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

@app.route('/categorias/roupas')
def pagina1():
    return render_template('pagina1.html')

@app.route('/categorias/futebol')
def pagina2():
    return render_template('pagina2.html')

@app.route('/categorias/basquete')
def pagina3():
    return render_template('pagina3.html')

@app.route('/categorias/volei')
def pagina4():
    return render_template('pagina4.html')

@app.route('/categorias/ciclismo')
def pagina5():
    return render_template('pagina5.html')

@app.route('/categorias/natação')
def pagina6():
    return render_template('pagina6.html')

@app.route('/categorias/tacos')
def pagina7():
    return render_template('pagina7.html')

@app.route('/categorias/automobilismo')
def pagina8():
    return render_template('pagina8.html')

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_image = request.form.get('product_image')
    product_description = request.form.get('product_description')

    if current_user.is_authenticated:
        user_cart_key = f'cart_{current_user.id}'
        cart = session.get(user_cart_key, [])
        if len(cart) >= 12:
            flash('Limite de 12 produtos no carrinho atingido.', 'warning')
        else:
            cart.append({'image': product_image, 'description': product_description})
            session[user_cart_key] = cart
            flash('Produto adicionado ao carrinho!', 'success')
    else:
        cart = session.get('cart', [])
        if len(cart) >= 12:
            flash('Limite de 12 produtos no carrinho atingido.', 'warning')
        else:
            cart.append({'image': product_image, 'description': product_description})
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

if __name__ == '__main__':
    app.run(debug=True)