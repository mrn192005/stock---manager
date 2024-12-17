from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_12345'

# Configuración para subida de archivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Asegurarse de que existe la carpeta de uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Base de datos simulada de usuarios
usuarios = {
    'admin@admin.com': {
        'password': 'admin123',
        'rol': 'admin',
        'nombre': 'Administrador'
    },
    'usuario@test.com': {
        'password': 'user123',
        'rol': 'usuario',
        'nombre': 'Usuario'
    }
}

productos = [
    {
        "id": 1,
        "nombre": "iPhone 15 Pro Max",
        "precio": 1299.99,
        "descuento": 10,
        "envio_gratis": True,
        "imagen": "https://picsum.photos/300/300?random=1",
        "vendedor": "Apple Store Official",
        "calificacion": 4.8,
        "categoria": "Smartphones",
        "stock": 15
    },
    {
        "id": 2,
        "nombre": "MacBook Pro M2",
        "precio": 1999.99,
        "descuento": 15,
        "envio_gratis": True,
        "imagen": "https://picsum.photos/300/300?random=2",
        "vendedor": "Apple Premium Reseller",
        "calificacion": 4.9,
        "categoria": "Laptops",
        "stock": 3
    },
    {
        "id": 3,
        "nombre": "Sony WH-1000XM5",
        "precio": 399.99,
        "descuento": 20,
        "envio_gratis": True,
        "imagen": "https://picsum.photos/300/300?random=3",
        "vendedor": "Sony Official Store",
        "calificacion": 4.7,
        "categoria": "Auriculares",
        "stock": 0
    }
]

carrito = []

@app.route('/')
def inicio():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', productos=productos, carrito=carrito)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email in usuarios and usuarios[email]['password'] == password:
            session['usuario'] = email
            session['rol'] = usuarios[email]['rol']
            session['nombre'] = usuarios[email]['nombre']
            
            if usuarios[email]['rol'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('inicio'))
        
        flash('Credenciales incorrectas')
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        nombre = request.form['nombre']
        rol = request.form['rol']
        
        if email not in usuarios:
            usuarios[email] = {
                'password': password,
                'rol': rol,
                'nombre': nombre
            }
            flash('Usuario registrado exitosamente')
            return redirect(url_for('login'))
        
        flash('El email ya está registrado')
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/tienda')
def tienda():
    if 'rol' not in session:
        return redirect(url_for('inicio'))
    return render_template('index.html', productos=productos, carrito=carrito)

@app.route('/admin')
def admin_dashboard():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('inicio'))
    
    # Calcular estadísticas
    total_productos = len(productos)
    productos_activos = sum(1 for p in productos if p['stock'] > 0)
    productos_stock_bajo = sum(1 for p in productos if 0 < p['stock'] <= 5)
    productos_sin_stock = sum(1 for p in productos if p['stock'] == 0)
    
    return render_template('admin_dashboard.html', 
                         productos=productos,
                         total_productos=total_productos,
                         productos_activos=productos_activos,
                         productos_stock_bajo=productos_stock_bajo,
                         productos_sin_stock=productos_sin_stock)

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('inicio'))
    
    try:
        # Validar datos básicos
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        categoria = request.form['categoria']
        
        if precio <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        if stock < 0:
            raise ValueError("El stock no puede ser negativo")
        
        # Manejar la imagen
        if 'imagen' not in request.files:
            flash('No se seleccionó ninguna imagen', 'error')
            return redirect(url_for('admin_dashboard'))
        
        file = request.files['imagen']
        if file.filename == '':
            flash('No se seleccionó ninguna imagen', 'error')
            return redirect(url_for('admin_dashboard'))

        if file and allowed_file(file.filename):
            # Crear nombre único para la imagen
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Guardar imagen
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Crear nuevo producto
            nuevo_producto = {
                "id": max([p['id'] for p in productos], default=0) + 1,
                "nombre": nombre,
                "precio": precio,
                "stock": stock,
                "categoria": categoria,
                "imagen": f"/static/uploads/{filename}",
                "descuento": int(request.form.get('descuento', 0)),
                "envio_gratis": 'envio_gratis' in request.form,
                "vendedor": session.get('nombre', 'Admin'),
                "calificacion": 5.0
            }
            
            productos.append(nuevo_producto)
            flash('Producto agregado exitosamente', 'success')
        else:
            flash('Formato de archivo no permitido. Use JPG, PNG o GIF', 'error')
            
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Error al agregar producto: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/eliminar_producto/<int:producto_id>')
def eliminar_producto(producto_id):
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('inicio'))
    
    global productos
    productos = [p for p in productos if p['id'] != producto_id]
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/actualizar_stock/<int:producto_id>/<int:cantidad>')
def actualizar_stock(producto_id, cantidad):
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('inicio'))
    
    producto = next((p for p in productos if p['id'] == producto_id), None)
    if producto:
        nuevo_stock = producto['stock'] + cantidad
        if nuevo_stock >= 0:
            producto['stock'] = nuevo_stock
            flash('Stock actualizado exitosamente', 'success')
        else:
            flash('El stock no puede ser negativo', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/buscar')
def buscar():
    busqueda = request.args.get('q', '').lower()
    productos_filtrados = [
        p for p in productos 
        if busqueda in p['nombre'].lower() or 
           busqueda in p['categoria'].lower()
    ]
    return render_template('index.html', productos=productos_filtrados, carrito=carrito)

@app.route('/categoria/<categoria>')
def categoria(categoria):
    productos_filtrados = [p for p in productos if p['categoria'] == categoria]
    return render_template('index.html', productos=productos_filtrados, carrito=carrito)

@app.route('/agregar_carrito/<int:producto_id>')
def agregar_carrito(producto_id):
    producto = next((p for p in productos if p['id'] == producto_id), None)
    if producto:
        carrito.append(producto)
    return redirect(url_for('inicio'))

@app.route('/carrito')
def ver_carrito():
    total = sum(p['precio'] * (1 - p['descuento']/100) for p in carrito)
    return render_template('carrito.html', carrito=carrito, total=total)

@app.route('/editar_producto/<int:producto_id>', methods=['POST'])
def editar_producto(producto_id):
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('inicio'))
    
    try:
        producto = next((p for p in productos if p['id'] == producto_id), None)
        if not producto:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('admin_dashboard'))

        # Actualizar datos básicos
        producto['nombre'] = request.form['nombre']
        producto['precio'] = float(request.form['precio'])
        producto['stock'] = int(request.form['stock'])
        producto['categoria'] = request.form['categoria']
        producto['descuento'] = int(request.form.get('descuento', 0))
        producto['envio_gratis'] = 'envio_gratis' in request.form

        # Manejar nueva imagen si se proporcionó una
        if 'imagen' in request.files and request.files['imagen'].filename != '':
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                producto['imagen'] = f"/static/uploads/{filename}"

        flash('Producto actualizado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al actualizar producto: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)