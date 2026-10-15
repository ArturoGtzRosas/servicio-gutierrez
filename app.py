from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import math
from fpdf import FPDF
import os
import hashlib
import smtplib
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Parche de compatibilidad para ReportLab en Python 3.8
_orig_md5 = hashlib.md5
def _patched_md5(*args, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _orig_md5(*args, **kwargs)
hashlib.md5 = _patched_md5
import io
from datetime import datetime
from flask import send_file

app = Flask(__name__)
app.secret_key = 'servicio_gutierrez_master_key_2026'

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'serviciogutierrezpc@gmail.com'
MAIL_PASSWORD = 'sondiuxeuddmtspx'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'servicio_gutierrez.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def enviar_presupuesto_correo(destinatario, cliente, equipo, total, folio, pdf_bytes):
    try:
        print(f"\n[CORREO] 1. Preparando cabeceras para: {destinatario}...")
        msg = MIMEMultipart()
        msg['From'] = f"Servicio Gutiérrez <{MAIL_USERNAME}>"
        msg['To'] = destinatario
        msg['Subject'] = f"Presupuesto de Servicio #{folio} - Servicio Gutiérrez"

        print("[CORREO] 2. Generando cuerpo HTML...")
        cuerpo_html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #1f3a5f; color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0; color: white;">Servicio Gutiérrez</h2>
                <p style="margin: 5px 0 0; font-size: 14px; color: #c5a356;">Mantenimiento y Reparación de Equipos</p>
            </div>
            <div style="padding: 25px;">
                <p>Estimado/a <strong>{cliente}</strong>,</p>
                <p>Esperamos que se encuentre muy bien. Le hacemos llegar la cotización formal para su equipo <strong>{equipo}</strong> (Folio #{folio}).</p>
                <div style="background-color: #f8f9fa; border-left: 4px solid #1f3a5f; padding: 12px 15px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 16px;"><strong>Monto Total:</strong> ${total:,.2f} MXN</p>
                </div>
                <p>Adjunto a este correo encontrará el archivo PDF con el desglose detallado de los conceptos.</p>
                <p>Cualquier duda o aclaración, quedamos a sus órdenes.</p>
                <br>
                <p style="margin-bottom: 2px;">Atentamente,</p>
                <p style="margin: 0; font-weight: bold; color: #1f3a5f;">Servicio Gutiérrez</p>
            </div>
        </div>
        """
        msg.attach(MIMEText(cuerpo_html, 'html', 'utf-8'))

        print("[CORREO] 3. Procesando adjunto PDF...")
        if isinstance(pdf_bytes, (bytes, bytearray)):
            contenido_pdf = pdf_bytes
        elif hasattr(pdf_bytes, 'getvalue'):
            contenido_pdf = pdf_bytes.getvalue()
        elif hasattr(pdf_bytes, 'read'):
            pdf_bytes.seek(0)
            contenido_pdf = pdf_bytes.read()
        else:
            contenido_pdf = str(pdf_bytes).encode('latin-1', errors='ignore')

        print(f"[CORREO] 3.1 Bytes obtenidos: {len(contenido_pdf)}. Empaquetando...")
        import base64
        
        # Codificación ultra rápida directa en C (milisegundos)
        pdf_b64 = base64.b64encode(contenido_pdf).decode('ascii')
        
        adjunto = MIMEBase('application', 'pdf')
        adjunto.set_payload(pdf_b64)
        adjunto['Content-Transfer-Encoding'] = 'base64'
        adjunto.add_header('Content-Disposition', 'attachment', filename=f"Presupuesto_{folio}.pdf")
        msg.attach(adjunto)

        print("[CORREO] 4. Conectando a smtp.gmail.com:587...")
        servidor = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        servidor.ehlo()
        servidor.starttls()
        servidor.ehlo()

        print("[CORREO] 5. Autenticando con Gmail...")
        servidor.login(MAIL_USERNAME, MAIL_PASSWORD)

        print("[CORREO] 6. Enviando...")
        servidor.sendmail(MAIL_USERNAME, destinatario, msg.as_string())
        servidor.quit()

        print("[CORREO] 7. ¡Envío completado exitosamente!")
        return True, "Correo enviado correctamente."

    except Exception as e:
        print(f"[CORREO ERROR] Falló en: {e}")
        return False, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cotizar_cliente')
def cotizar_cliente():
    return render_template('cotizar_cliente.html')

@app.route('/procesar_cotizacion', methods=['POST'])
def procesar_cotizacion():
    nombre = request.form['nombre']
    servicio = request.form['servicio']
    modelo = request.form['modelo']
    
    db = get_db_connection()
    db.execute("INSERT INTO cotizaciones (nombre, servicio, modelo) VALUES (?, ?, ?)",
               (nombre, servicio, modelo))
    db.commit()
    db.close()
    
    return render_template('confirmacion.html', nombre=nombre, servicio=servicio, modelo=modelo)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        asunto = request.form.get('asunto', '').strip()
        mensaje = request.form.get('mensaje', '').strip()
        
        db = get_db_connection()
        db.execute('''CREATE TABLE IF NOT EXISTS mensajes 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, email TEXT, telefono TEXT, asunto TEXT, mensaje TEXT, leido INTEGER DEFAULT 0)''')
        try:
            db.execute("ALTER TABLE mensajes ADD COLUMN asunto TEXT")
        except:
            pass
            
        db.execute('''INSERT INTO mensajes (fecha, nombre, email, telefono, asunto, mensaje) 
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, email, telefono, asunto, mensaje))
        db.commit()
        db.close()
        
        return render_template('confirmacion.html', nombre=nombre, servicio=asunto, modelo="Mensaje de Contacto")
        
    return render_template('contacto.html')

@app.route('/cotizador', methods=['GET', 'POST'])
def cotizador():
    total = 0
    seleccionados = []
    notas_cliente = ""
    if request.method == 'POST':
        opciones = {
            'Limpieza Básica': 450, 'Limpieza Profunda': 650,
            'S.O. Estándar': 400, 'S.O. + Respaldo': 600,
            'SSD 240GB': 1200, 'SSD 480GB': 1600,
            'RAM 8GB': 850, 'RAM 16GB': 1500,
            'Office/Software': 600, 'Antivirus 1 Año': 500,
            'Batería Compatible': 950, 'Batería Original': 1400,
            'Pantalla HD': 1800, 'Pantalla FHD': 2400
        }
        for cat in ['mantenimiento', 'sistema', 'ssd', 'ram', 'software', 'bateria', 'pantalla']:
            val = request.form.get(cat)
            if val in opciones:
                total += opciones[val]
                seleccionados.append(f"{val} (${opciones[val]})")
        
        if request.form.get('urgente'):
            total += 250
            seleccionados.append("SERVICIO EXPRESS ($250)")
            
        notas_cliente = request.form.get('observaciones', '').strip()
        servicios_final = ", ".join(seleccionados)
        if notas_cliente: servicios_final += f" | NOTAS: {notas_cliente}"
        
        if total > 0:
            db = get_db_connection()
            db.execute("INSERT INTO presupuestos (servicios, total) VALUES (?, ?)", (servicios_final, total))
            db.commit()
            db.close()
            
    return render_template('cotizador.html', total=total, seleccion=seleccionados, notas=notas_cliente)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db_connection()
        user = db.execute("SELECT * FROM usuarios WHERE email = ?", (request.form['email'],)).fetchone()
        db.close()
        if user and user['password'] == request.form['password']:
            session['user_id'] = user['id']
            session['user_name'] = user['nombre']
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/ver_cotizaciones')
def ver_cotizaciones():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db_connection()
    datos = db.execute("SELECT * FROM cotizaciones ORDER BY id DESC").fetchall()
    db.close()
    return render_template('admin_cotizaciones.html', cotizaciones=datos)

@app.route('/ver_mensajes')
def ver_mensajes():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db_connection()
    # Asegura que la tabla exista antes de consultarla
    db.execute('''CREATE TABLE IF NOT EXISTS mensajes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, email TEXT, telefono TEXT, mensaje TEXT, leido INTEGER DEFAULT 0)''')
    db.commit()
    datos = db.execute("SELECT * FROM mensajes ORDER BY id DESC").fetchall()
    db.close()
    return render_template('admin_mensajes.html', mensajes=datos)

@app.route('/ver_presupuestos')
def ver_presupuestos():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db_connection()
    datos = db.execute("SELECT * FROM presupuestos ORDER BY id DESC").fetchall()
    db.close()
    return render_template('admin_presupuestos.html', presupuestos=datos)

@app.route('/descargar_presupuesto/<int:id>')
def descargar_presupuesto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db_connection()
    p = db.execute("SELECT * FROM presupuestos WHERE id = ?", (id,)).fetchone()
    db.close()
    
    if not p:
        flash('Presupuesto no encontrado.')
        return redirect(url_for('ver_presupuestos'))
        
    folio = 1000 + p['id']
    cliente = p['cliente'] if p['cliente'] else 'Cliente'
    telefono = p['telefono'] if p['telefono'] else ''
    equipo = p['equipo'] if p['equipo'] else ''
    total = float(p['total']) if p['total'] else 0.0
    
    # Reconstruir los renglones guardados
    items = []
    if p['servicios']:
        for serv in p['servicios'].split(', '):
            items.append({'cant': 1, 'desc': serv, 'precio': total})
            
    pdf_buffer = generar_pdf_presupuesto(folio, cliente, telefono, equipo, items, total)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Presupuesto_{cliente.replace(' ', '_')}_{folio}.pdf",
        mimetype='application/pdf'
    )

@app.route('/enviar_presupuesto_email/<int:id>', methods=['GET', 'POST'])
def enviar_presupuesto_email(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    email_destino = request.form.get('email_destino') or request.args.get('email_destino')

    if not email_destino:
        flash("Por favor proporciona un correo electrónico válido.")
        return redirect(url_for('ver_presupuestos'))

    conn = get_db_connection()
    presupuesto = conn.execute('SELECT * FROM presupuestos WHERE id = ?', (id,)).fetchone()
    conn.close()

    if not presupuesto:
        flash("Presupuesto no encontrado.")
        return redirect(url_for('ver_presupuestos'))

    # Generar el PDF
    try:
        folio = 1000 + presupuesto['id']
        cliente = presupuesto['cliente'] if presupuesto['cliente'] else 'Cliente'
        telefono = presupuesto['telefono'] if presupuesto['telefono'] else ''
        equipo = presupuesto['equipo'] if presupuesto['equipo'] else 'General'
        total = presupuesto['total'] if presupuesto['total'] else 0.0

        items = []
        if presupuesto['servicios']:
            for serv in presupuesto['servicios'].split(', '):
                items.append({'cant': 1, 'desc': serv, 'precio': total})

        pdf_buffer = generar_pdf_presupuesto(folio, cliente, telefono, equipo, items, total)
        pdf_bytes = pdf_buffer.getvalue()
    except Exception as e:
        print(f"Error generando PDF: {e}")
        flash(f"Error al generar el PDF: {e}")
        return redirect(url_for('ver_presupuestos'))

    # Enviar correo
    exito, mensaje = enviar_presupuesto_correo(
        destinatario=email_destino,
        cliente=cliente,
        equipo=equipo,
        total=total,
        folio=folio,
        pdf_bytes=pdf_bytes
    )

    if exito:
        flash(f"Presupuesto enviado exitosamente a {email_destino}")
    else:
        flash(f"No se pudo enviar el correo: {mensaje}")

    return redirect(url_for('ver_presupuestos'))

@app.route('/borrar_presupuesto/<int:id>')
def borrar_presupuesto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db_connection()
    db.execute("DELETE FROM presupuestos WHERE id = ?", (id,))
    db.commit()
    db.close()
    
    return redirect(url_for('ver_presupuestos'))

@app.route('/borrar_mensaje/<int:id>')
def borrar_mensaje(id):
    db = get_db_connection()
    db.execute("DELETE FROM mensajes WHERE id = ?", (id,))
    db.commit()
    db.close()
    return redirect(url_for('ver_mensajes'))

@app.route('/borrar_cotizacion/<int:id>')
def borrar_cotizacion(id):
    db = get_db_connection()
    db.execute("DELETE FROM cotizaciones WHERE id = ?", (id,))
    db.commit()
    db.close()
    return redirect(url_for('ver_cotizaciones'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/crear_presupuesto', methods=['GET', 'POST'])
def crear_presupuesto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        cliente = request.form.get('cliente', '').strip()
        telefono = request.form.get('telefono', '').strip()
        equipo = request.form.get('equipo', '').strip()
        
        cantidades = request.form.getlist('cantidad[]')
        descripciones = request.form.getlist('descripcion[]')
        precios = request.form.getlist('precio[]')
        
        items = []
        total = 0.0
        for c, d, p in zip(cantidades, descripciones, precios):
            if d.strip() and p.strip():
                try:
                    cant = int(c) if c.strip() else 1
                except ValueError:
                    cant = 1
                try:
                    precio = float(p)
                except ValueError:
                    precio = 0.0
                    
                items.append({'cant': cant, 'desc': d.strip(), 'precio': precio})
                total += cant * precio
        
        db = get_db_connection()
        db.execute('''CREATE TABLE IF NOT EXISTS presupuestos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, 
                       telefono TEXT, equipo TEXT, servicios TEXT, total REAL)''')
        
        servicios_resumen = ", ".join([f"(x{it['cant']}) {it['desc']}" for it in items])
        cursor = db.execute('''INSERT INTO presupuestos (fecha, cliente, telefono, equipo, servicios, total)
                               VALUES (?, ?, ?, ?, ?, ?)''',
                            (datetime.now().strftime("%d/%m/%Y %H:%M"), cliente, telefono, equipo, servicios_resumen, total))
        db.commit()
        
        folio = 1000 + cursor.lastrowid
        db.close()

        pdf_buffer = generar_pdf_presupuesto(folio, cliente, telefono, equipo, items, total)
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"Presupuesto_{cliente.replace(' ', '_')}_{folio}.pdf",
            mimetype='application/pdf'
        )

    return render_template('generar_presupuesto.html')

class PDFPresupuesto(FPDF):
    def rotate(self, angle, x=None, y=None):
        if x is None: x = self.x
        if y is None: y = self.y
        self._out(f"q {math.cos(math.radians(angle))} {math.sin(math.radians(angle))} {-math.sin(math.radians(angle))} {math.cos(math.radians(angle))} {x * self.k} {(self.h - y) * self.k} cm 1 0 0 1 {-x * self.k} {-(self.h - y) * self.k} cm")

    def end_rotate(self):
        self._out("Q")

    def header(self):
        self.set_fill_color(27, 48, 91)
        self.rect(0, 0, 210, 50, 'F')
        
        logo_local = os.path.join(BASE_DIR, "static", "img", "logo_nuevo.png")
        url_logo_web = "https://i.postimg.cc/wvXCKc44/logo.png"
        try:
            if os.path.exists(logo_local):
                self.image(logo_local, 10, 6, 42)
            else:
                self.image(url_logo_web, 10, 6, 42)
        except Exception:
            pass
        
        self.set_text_color(197, 160, 89)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 10, 'SERVICIO TÉCNICO GUTIÉRREZ', ln=True, align='C')
        
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', '', 9)
        self.cell(0, 5, 'Francisco Arturo Gutiérrez Rosas | RFC: GURF770808', ln=True, align='C')
        self.cell(0, 5, 'Cda. Águilas mz 13 lt 30 Casa D, San Buenaventura, Ixtapaluca, México. 56536', ln=True, align='C')
        self.cell(0, 5, 'Tel. 55 4031 3150 | e-mail: arturogtzrosass@gmail.com', ln=True, align='C')
        self.ln(25)

    def marca_de_agua(self):
        self.set_font('Arial', 'B', 30)
        self.set_text_color(240, 240, 240)
        self.rotate(45, 105, 160)
        texto = "PRESUPUESTO   PRESUPUESTO   PRESUPUESTO"
        w = self.get_string_width(texto)
        self.text(105 - (w / 2), 160, texto)
        self.end_rotate()

    def footer(self):
        self.set_y(-22)
        self.set_font('Arial', 'B', 8.5)
        self.set_text_color(200, 0, 0)
        self.cell(0, 5, '* AVISO: Este presupuesto puede cambiar sin previo aviso y tiene vigencia de 15 días.', align='C', ln=True)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, 'Servicio Gutiérrez - Calidad y Honestidad en cada reparación', align='C')


def generar_pdf_presupuesto(folio, cliente, telefono, equipo, items, total):
    subtotal = total / 1.16
    iva = total - subtotal
    
    pdf = PDFPresupuesto()
    pdf.add_page()
    pdf.marca_de_agua()
    
    pdf.set_xy(150, 55)
    pdf.set_text_color(200, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(50, 10, f'FOLIO: {folio}', ln=True, align='R')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'PRESUPUESTO / COTIZACIÓN', ln=True, align='C')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 7, f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True, align='R')
    pdf.ln(5)

    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' DATOS DEL CLIENTE Y EQUIPO', ln=True, fill=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'  Cliente: {cliente}', ln=True)
    if telefono: pdf.cell(0, 6, f'  Teléfono: {telefono}', ln=True)
    pdf.cell(0, 6, f'  Equipo: {equipo if equipo else "General"}', ln=True)
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(15, 8, 'Cant.', 1, 0, 'C', True)
    pdf.cell(105, 8, 'Descripción del Servicio / Artículos', 1, 0, 'C', True)
    pdf.cell(35, 8, 'Precio Unit.', 1, 0, 'C', True)
    pdf.cell(35, 8, 'Importe', 1, 1, 'C', True)
    pdf.set_font('Arial', '', 10)
    
    for item in items:
        cant = item.get('cant', 1)
        desc = item.get('desc', '')
        precio_unit = float(item.get('precio', 0.0))
        importe_renglon = precio_unit * cant
        
        pdf.cell(15, 8, f" {cant}", 1, 0, 'C')
        pdf.cell(105, 8, f" {desc}", 1, 0, 'L')
        pdf.cell(35, 8, f"${precio_unit:,.2f}", 1, 0, 'R')
        pdf.cell(35, 8, f"${importe_renglon:,.2f}", 1, 1, 'R')
    
    pdf.ln(4)
    pdf.cell(155, 7, 'Subtotal:', 0, 0, 'R')
    pdf.cell(35, 7, f'${subtotal:,.2f}', 0, 1, 'R')
    
    pdf.cell(155, 7, 'I.V.A. (16%):', 0, 0, 'R')
    pdf.cell(35, 7, f'${iva:,.2f}', 0, 1, 'R')
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(155, 9, 'TOTAL PRESUPUESTADO (IVA inc):', 1, 0, 'R', True)
    pdf.cell(35, 9, f'${total:,.2f}', 1, 1, 'R', True)
    
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin-1')
    return io.BytesIO(pdf_bytes)

# =====================================================
# MÓDULO DE NOTAS DE VENTA (INTEGRACIÓN)
# =====================================================

def init_tabla_notas():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS notas_venta 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, 
                     direccion TEXT, telefono TEXT, equipo TEXT, servicio TEXT, total REAL, observaciones TEXT)''')
    conn.commit()
    conn.close()

init_tabla_notas()

class PDFNotaVenta(FPDF):
    def rotate(self, angle, x=None, y=None):
        if x is None: x = self.x
        if y is None: y = self.y
        self._out(f"q {math.cos(math.radians(angle))} {math.sin(math.radians(angle))} {-math.sin(math.radians(angle))} {math.cos(math.radians(angle))} {x * self.k} {(self.h - y) * self.k} cm 1 0 0 1 {-x * self.k} {-(self.h - y) * self.k} cm")

    def end_rotate(self):
        self._out("Q")

    def header(self):
        self.set_fill_color(27, 48, 91)
        self.rect(0, 0, 210, 50, 'F')
        
        logo_local = os.path.join(BASE_DIR, "static", "img", "logo_nuevo.png")
        url_logo_web = "https://i.postimg.cc/wvXCKc44/logo.png"
        try:
            if os.path.exists(logo_local):
                self.image(logo_local, 10, 6, 42)
            else:
                self.image(url_logo_web, 10, 6, 42)
        except Exception:
            pass
        
        self.set_text_color(197, 160, 89)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 10, 'SERVICIO TÉCNICO GUTIÉRREZ', ln=True, align='C')
        
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', '', 9)
        self.cell(0, 5, 'Francisco Arturo Gutiérrez Rosas | RFC: GURF770808', ln=True, align='C')
        self.cell(0, 5, 'Cda. Águilas mz 13 lt 30 Casa D, San Buenaventura, Ixtapaluca, México. 56536', ln=True, align='C')
        self.cell(0, 5, 'Tel. 55 4031 3150 | e-mail: arturogtzrosass@gmail.com', ln=True, align='C')
        self.ln(25)

    def marca_de_agua(self):
        self.set_font('Arial', 'B', 30)
        self.set_text_color(240, 240, 240)
        self.rotate(45, 105, 160)
        texto = "ESTE NO ES UN COMPROBANTE FISCAL"
        w = self.get_string_width(texto)
        self.text(105 - (w / 2), 160, texto)
        self.end_rotate()

    def footer(self):
        self.set_y(-22)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(27, 48, 91)
        self.cell(0, 5, '** Todo trabajo tiene 30 días de garantía en mano de obra', align='C', ln=True)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, 'Servicio Gutiérrez - Calidad y Honestidad en cada reparación', align='C')

def generar_pdf_nota_binario(folio, cliente, direccion, telefono, equipo, servicios_items, total, obs=""):
    subtotal = total / 1.16
    iva = total - subtotal
    pdf = PDFNotaVenta()
    pdf.add_page()
    pdf.marca_de_agua()
    
    # Encabezado folio y título
    pdf.set_xy(140, 55)
    pdf.set_text_color(200, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(60, 10, f'FOLIO: {folio}', ln=True, align='R')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 8, 'NOTA DE VENTA', ln=True, align='C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True, align='R')
    pdf.ln(4)

    # Datos del cliente y equipo
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, ' DATOS DEL CLIENTE Y EQUIPO', ln=True, fill=True)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'  Cliente: {cliente}', ln=True)
    if direccion: pdf.cell(0, 6, f'  Dirección: {direccion}', ln=True)
    if telefono: pdf.cell(0, 6, f'  Teléfono: {telefono}', ln=True)
    pdf.cell(0, 6, f'  Equipo: {equipo}', ln=True)
    if obs: pdf.multi_cell(0, 6, f'  Observaciones: {obs}')
    pdf.ln(5)

    # Encabezado de la tabla (Ancho total: 15 + 105 + 35 + 35 = 190 mm)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(15, 8, 'Cant.', 1, 0, 'C', True)
    pdf.cell(105, 8, 'Descripción del Servicio / Artículo', 1, 0, 'L', True)
    pdf.cell(35, 8, 'P. Unitario', 1, 0, 'R', True)
    pdf.cell(35, 8, 'Importe', 1, 1, 'R', True)
    pdf.set_font('Arial', '', 9)

    for item in servicios_items:
        cant = item.get('cant', 1)
        desc = item.get('desc', '')
        p_unit = item.get('p_unit', float(item.get('precio', 0.0)) / cant)
        # Importe real directo (Cantidad x Precio Unitario)
        importe_item = cant * p_unit

        pdf.cell(15, 8, f"{cant}", 1, 0, 'C')
        pdf.cell(105, 8, f" {desc}", 1, 0, 'L')
        pdf.cell(35, 8, f"${p_unit:,.2f}", 1, 0, 'R')
        pdf.cell(35, 8, f"${importe_item:,.2f}", 1, 1, 'R')

    pdf.ln(4)
    # Bloque de liquidación final
    pdf.set_font('Arial', '', 10)
    pdf.cell(155, 6, 'Subtotal:', 0, 0, 'R')
    pdf.cell(35, 6, f'${subtotal:,.2f}', 0, 1, 'R')
    
    pdf.cell(155, 6, 'I.V.A. (16%):', 0, 0, 'R')
    pdf.cell(35, 6, f'${iva:,.2f}', 0, 1, 'R')
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(155, 9, 'TOTAL A PAGAR (IVA inc):', 1, 0, 'R', True)
    pdf.cell(35, 9, f'${total:,.2f}', 1, 1, 'R', True)
    
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin-1')
    return io.BytesIO(pdf_bytes)

@app.route('/ver_notas')
def ver_notas():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db_connection()
    notas = db.execute("SELECT * FROM notas_venta ORDER BY id DESC").fetchall()
    db.close()
    return render_template('admin_notas.html', notas=notas)

@app.route('/crear_nota', methods=['GET', 'POST'])
def crear_nota():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        cliente = request.form.get('cliente', '').strip()
        direccion = request.form.get('direccion', '').strip()
        telefono = request.form.get('telefono', '').strip()
        equipo = request.form.get('equipo', '').strip()
        observaciones = request.form.get('observaciones', '').strip()
        
        cantidades = request.form.getlist('cantidad[]')
        descripciones = request.form.getlist('descripcion[]')
        precios = request.form.getlist('precio[]')
        
        items = []
        total = 0.0
        for c, d, p in zip(cantidades, descripciones, precios):
            if d.strip() and p.strip():
                try: cant = int(c) if c.strip() else 1
                except: cant = 1
                try: precio_u = float(p)
                except: precio_u = 0.0
                
                subt_item = cant * precio_u
                items.append({
                    'cant': cant,
                    'desc': d.strip(),
                    'p_unit': precio_u,
                    'precio': subt_item
                })
                total += subt_item
                
        serv_resumen = ", ".join([f"(x{it['cant']}) {it['desc']}" if it['cant'] > 1 else it['desc'] for it in items])
        
        db = get_db_connection()
        cur = db.execute('''INSERT INTO notas_venta 
                            (fecha, cliente, direccion, telefono, equipo, servicio, total, observaciones) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                         (datetime.now().strftime("%d/%m/%Y %H:%M"), cliente, direccion, telefono, equipo, serv_resumen, total, observaciones))
        db.commit()
        folio = 1000 + cur.lastrowid
        db.close()
        
        pdf_buf = generar_pdf_nota_binario(folio, cliente, direccion, telefono, equipo, items, total, observaciones)
        return send_file(
            pdf_buf,
            as_attachment=True,
            download_name=f"Nota_{cliente.replace(' ', '_')}_{folio}.pdf",
            mimetype='application/pdf'
        )

    return render_template('generar_nota.html')

@app.route('/descargar_nota/<int:id>')
def descargar_nota(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db_connection()
    n = db.execute("SELECT * FROM notas_venta WHERE id = ?", (id,)).fetchone()
    db.close()
    if not n:
        flash("Nota no encontrada.")
        return redirect(url_for('ver_notas'))
        
    folio = 1000 + n['id']
    items = []
    if n['servicio']:
        for s in n['servicio'].split(', '):
            items.append({'desc': s, 'precio': n['total']})
            
    pdf_buf = generar_pdf_nota_binario(folio, n['cliente'], n['direccion'], n['telefono'], n['equipo'], items, float(n['total']), n['observaciones'])
    return send_file(
        pdf_buf,
        as_attachment=True,
        download_name=f"Nota_{n['cliente'].replace(' ', '_')}_{folio}.pdf",
        mimetype='application/pdf'
    )

@app.route('/borrar_nota/<int:id>')
def borrar_nota(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db_connection()
    db.execute("DELETE FROM notas_venta WHERE id = ?", (id,))
    db.commit()
    db.close()
    flash("Nota eliminada correctamente.")
    return redirect(url_for('ver_notas'))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)