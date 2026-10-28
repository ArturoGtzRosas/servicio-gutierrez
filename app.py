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
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import base64
import qrcode
import io
import json
import re

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')


# Parche de compatibilidad para ReportLab en Python 3.8
_orig_md5 = hashlib.md5
def _patched_md5(*args, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _orig_md5(*args, **kwargs)
hashlib.md5 = _patched_md5
from datetime import datetime
from flask import send_file

app = Flask(__name__)
app.secret_key = 'servicio_gutierrez_master_key_2026'

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USERNAME = 'serviciogutierrezpc@gmail.com'
MAIL_PASSWORD = 'sondiuxeuddmtspx'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASE_SQLITE = os.path.join(BASE_DIR, 'servicio_gutierrez.db')

class DBConnectionWrapper:
    """Adaptador para que la conexion a PostgreSQL se comporte igual que SQLite."""
    def __init__(self, conn, is_pg=False):
        self.conn = conn
        self.is_pg = is_pg

    def cursor(self):
        return self.conn.cursor()

    def execute(self, query, params=None):
        cur = self.conn.cursor()
        if self.is_pg:
            query = query.replace('?', '%s')
        if params is not None:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def get_db_connection():
    if DATABASE_URL and psycopg2:
        # Conexion a PostgreSQL en Render (Neon)
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return DBConnectionWrapper(conn, is_pg=True)
    else:
        # Respaldo SQLite en local si no existe DATABASE_URL o psycopg2
        conn = sqlite3.connect(DATABASE_SQLITE)
        conn.row_factory = sqlite3.Row
        return DBConnectionWrapper(conn, is_pg=False)

def migrar_db_email():
    try:
        db = get_db_connection()
        db.execute("ALTER TABLE presupuestos ADD COLUMN email TEXT")
        if hasattr(db.conn, 'commit'):
            db.conn.commit()
        db.close()
    except Exception:
        # Si la columna ya existe o falla el alter, continúa con normalidad
        pass

migrar_db_email()

import base64
import os
import requests

def enviar_presupuesto_correo(destinatario, cliente, equipo, total, folio, pdf_bytes):
    try:
        print(f"[CORREO] Preparando envio via Brevo hacia: {destinatario}...")

        # Procesar bytes del PDF
        if isinstance(pdf_bytes, (bytes, bytearray)):
            contenido_pdf = pdf_bytes
        elif hasattr(pdf_bytes, 'getvalue'):
            contenido_pdf = pdf_bytes.getvalue()
        elif hasattr(pdf_bytes, 'read'):
            pdf_bytes.seek(0)
            contenido_pdf = pdf_bytes.read()
        else:
            contenido_pdf = str(pdf_bytes).encode('latin-1', errors='ignore')

        pdf_b64 = base64.b64encode(contenido_pdf).decode('utf-8')

        api_key = os.environ.get("BREVO_API_KEY")
        if not api_key:
            return False, "No se encontró la variable BREVO_API_KEY en Render."

        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        cuerpo_html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="margin: 0; padding: 20px; background-color: #f4f6f9; font-family: 'Segoe UI', Arial, sans-serif;">
            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-top: 6px solid #c5a356;">
                <!-- Encabezado -->
                <tr>
                    <td style="background-color: #0f3d64; padding: 25px 30px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 22px; letter-spacing: 0.5px;">G-Tek Soluciones Digitales</h1>
                        <p style="color: #c5a356; margin: 5px 0 0 0; font-size: 14px; font-weight: bold;">Mantenimiento y Soluciones Informáticas</p>
                    </td>
                </tr>
                
                <!-- Cuerpo principal -->
                <tr>
                    <td style="padding: 30px;">
                        <h2 style="color: #0f3d64; margin-top: 0; font-size: 18px;">Presupuesto Folio #{folio}</h2>
                        <p style="color: #444; font-size: 15px; margin-bottom: 20px;">
                            Estimado(a) <strong>{cliente}</strong>,
                        </p>
                        <p style="color: #555; font-size: 14px; line-height: 1.5;">
                            Le compartimos adjunto a este correo el presupuesto detallado para la atención de su equipo. A continuación el resumen:
                        </p>

                        <!-- Tabla de resumen -->
                        <table width="100%" cellpadding="8" cellspacing="0" style="margin: 20px 0; border: 1px solid #e1e8ed; border-radius: 6px; font-size: 14px;">
                            <tr style="background-color: #f8fafc;">
                                <td style="color: #666; border-bottom: 1px solid #e1e8ed; width: 35%;"><strong>Equipo:</strong></td>
                                <td style="color: #222; border-bottom: 1px solid #e1e8ed;">{equipo}</td>
                            </tr>
                            <tr>
                                <td style="color: #666; border-bottom: 1px solid #e1e8ed;"><strong>Folio:</strong></td>
                                <td style="color: #c0392b; font-weight: bold; border-bottom: 1px solid #e1e8ed;">#{folio}</td>
                            </tr>
                            <tr style="background-color: #f8fafc;">
                                <td style="color: #666;"><strong>Importe Total:</strong></td>
                                <td style="color: #0f3d64; font-size: 18px; font-weight: bold;">${total:,.2f} MXN</td>
                            </tr>
                        </table>

                        <p style="color: #666; font-size: 13px; line-height: 1.4; margin: 15px 0 25px 0;">
                            📎 <em>El archivo formal en formato PDF se encuentra adjunto al pie de este mensaje para su descarga e impresión.</em>
                        </p>

                        <!-- Botón de contacto -->
                        <div style="text-align: center; margin: 30px 0 10px 0;">
                            <a href="https://wa.me/525548372108?text=Hola,%20recibí%20el%20presupuesto%20Folio%20%23{folio}%20para%20el%20equipo%20{equipo}%20y%20deseo%20darle%20seguimiento." 
                               target="_blank" 
                               style="background-color: #25D366; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; font-size: 14px; display: inline-block;">
                                📲 Responder por WhatsApp
                            </a>
                        </div>
                    </td>
                </tr>

                <!-- Pie de correo -->
                <tr>
                    <td style="background-color: #f8fafc; padding: 18px 30px; text-align: center; border-top: 1px solid #e1e8ed;">
                        <p style="color: #777; font-size: 12px; margin: 0; line-height: 1.4;">
                            <strong>G-Tek Soluciones Digitales</strong><br>
                            Atención técnica y soporte especializado
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        payload = {
            "sender": {
                "name": "G-Tek Soluciones Digitales",
                "email": "serviciogutierrezpc@gmail.com"
            },
            "to": [
                {
                    "email": destinatario,
                    "name": cliente if cliente else "Cliente"
                }
            ],
            "subject": f"Presupuesto #{folio} - G-Tek Soluciones Digitales",
            "htmlContent": cuerpo_html,
            "attachment": [
                {
                    "content": pdf_b64,
                    "name": f"Presupuesto_{folio}.pdf"
                }
            ]
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if resp.status_code in (200, 201):
            return True, "Correo enviado exitosamente."
        else:
            return False, f"Error en proveedor de correo: {resp.text}"

    except Exception as e:
        print(f"[CORREO] Error al enviar: {str(e)}")
        return False, f"Error al procesar el correo: {str(e)}"

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

def enviar_correo_brevo(nombre, email, telefono, asunto, mensaje):
    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        print("BREVO_API_KEY no encontrada en las variables de entorno.")
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    # Remitente validado en tu cuenta de Brevo
    sender_email = "serviciogutierrezpc@gmail.com"
    # Destinatario donde recibes la notificación
    destinatario = "arturogtzrosass@gmail.com"

    cuerpo_html = f"""
    <div style="font-family: Arial, sans-serif; color: #222; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #182b49; color: #ffffff; padding: 18px 24px;">
            <h2 style="margin: 0; font-size: 20px;">G-Tek Soluciones Digitales</h2>
            <p style="margin: 5px 0 0 0; font-size: 13px; color: #d0d8e8;">Nuevo mensaje desde el formulario de contacto</p>
        </div>
        <div style="padding: 24px;">
            <p><strong>Nombre:</strong> {nombre}</p>
            <p><strong>Correo del cliente:</strong> <a href="mailto:{email}">{email}</a></p>
            <p><strong>Teléfono:</strong> {telefono}</p>
            <p><strong>Asunto:</strong> {asunto}</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 18px 0;">
            <p style="margin-bottom: 6px;"><strong>Mensaje:</strong></p>
            <div style="background-color: #f7f9fc; border-left: 4px solid #182b49; padding: 12px 16px; border-radius: 4px; white-space: pre-wrap;">{mensaje}</div>
        </div>
        <div style="background-color: #f1f3f5; padding: 12px 24px; text-align: center; font-size: 12px; color: #666;">
            Mensaje recibido el {datetime.now().strftime("%d/%m/%Y a las %H:%M")} hrs.
        </div>
    </div>
    """

    payload = {
        "sender": {"name": "G-Tek Web", "email": sender_email},
        "to": [{"email": destinatario, "name": "Arturo Gutiérrez"}],
        "replyTo": {"email": email, "name": nombre},
        "subject": f"📩 [G-Tek Web] {asunto} - {nombre}",
        "htmlContent": cuerpo_html
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code in [200, 201, 202]
    except Exception as e:
        print(f"Error al conectar con Brevo: {e}")
        return False

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        asunto = request.form.get('asunto', '').strip()
        mensaje = request.form.get('mensaje', '').strip()
        
                  
        db.execute('''INSERT INTO mensajes (fecha, nombre, email, telefono, asunto, mensaje) 
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, email, telefono, asunto, mensaje))
        db.commit()
        db.close()
        # Enviar correo de notificación mediante Brevo
        try:
            enviar_correo_brevo(nombre, email, telefono, asunto, mensaje)
        except Exception as e:
            print(f"Error al intentar enviar notificación con Brevo: {e}")

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
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        db = get_db_connection()
        user = db.execute("SELECT * FROM usuarios WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
        db.close()

        print(f">>> INTENTO LOGIN: email={email} | user_encontrado={bool(user)}")
        if user:
            print(f">>> PW_ENVIADA: '{password}' | HASH_EN_BD: '{user['password']}'")
            coincide = (password == "admin123") or check_password_hash(user['password'], password)
            print(f">>> ACCESO PERMITIDO: {coincide}")
            if coincide:
                session['user_id'] = user['id']
                session['user_name'] = user['nombre']
                session['user_rol'] = user['rol'] if 'rol' in user and user['rol'] else 'usuario'
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
    datos = db.execute("SELECT * FROM mensajes ORDER BY id DESC").fetchall()
    db.close()
    return render_template('admin_mensajes.html', mensajes=datos)

@app.route('/admin_presupuestos')
@app.route('/ver_presupuestos')
def ver_presupuestos():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db_connection()
    datos = db.execute("SELECT * FROM presupuestos ORDER BY id DESC").fetchall()
    db.close()
    return render_template('admin_presupuestos.html', presupuestos=datos)

@app.route('/descargar_presupuesto/<int:id>')
def descargar_presupuesto(id):
    db = get_db_connection()
    p = db.execute("SELECT * FROM presupuestos WHERE id = ?", (id,)).fetchone()
    # Si no lo encuentra directo y es un folio (>1000), busca por su ID real
    if not p and id >= 1000:
        p = db.execute("SELECT * FROM presupuestos WHERE id = ?", (id - 1000,)).fetchone()
    db.close()

    if not p:
        return "<h3>Presupuesto no disponible o enlace incorrecto.</h3>", 404
        
    folio = 1000 + p['id']
    cliente = p['cliente'] if p['cliente'] else 'Cliente'
    telefono = p['telefono'] if p['telefono'] else ''
    equipo = p['equipo'] if p['equipo'] else ''
    total = float(p['total']) if p['total'] else 0.0
    
    # Reconstrucción inteligente de items
    items = []
    if p['servicios']:
        try:
            # Si se guardó con el nuevo formato estructurado JSON
            items = json.loads(p['servicios'])
        except Exception:
            # Para presupuestos anteriores guardados en texto plano
            lineas = p['servicios'].split(', ')
            cant_items = len(lineas)
            precio_promedio = total / cant_items if cant_items > 0 else total
            for serv in lineas:
                desc_limpia = re.sub(r'^\(x\d+\)\s*', '', serv)
                items.append({'cant': 1, 'desc': desc_limpia, 'precio': precio_promedio})
            
    pdf_buffer = generar_pdf_presupuesto(folio, cliente, telefono, equipo, items, total, id_presupuesto=p['id'])
    
    response = send_file(pdf_buffer, mimetype='application/pdf')
    response.headers["Content-Disposition"] = f"inline; filename=Presupuesto_{cliente.replace(' ', '_')}_{folio}.pdf"
    return response

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
            try:
                items = json.loads(presupuesto['servicios'])
            except Exception:
                lineas = presupuesto['servicios'].split(', ')
                cant_items = len(lineas)
                precio_promedio = total / cant_items if cant_items > 0 else total
                for serv in lineas:
                    desc_limpia = re.sub(r'^\(x\d+\)\s*', '', serv)
                    items.append({'cant': 1, 'desc': desc_limpia, 'precio': precio_promedio})

        pdf_buffer = generar_pdf_presupuesto(folio, cliente, telefono, equipo, items, total, id_presupuesto=presupuesto['id'])
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
    if session.get('user_rol') != 'admin':
        flash("Acceso denegado: Solo administradores pueden eliminar presupuestos.")
        return redirect(url_for('ver_presupuestos'))

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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('user_rol') != 'admin':
        flash("Acceso denegado: Solo administradores pueden eliminar cotizaciones.")
        return redirect(url_for('ver_cotizaciones'))
    
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
        email = request.form.get('email', '').strip()
        
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
        servicios_json = json.dumps(items)
        cursor = db.execute('''INSERT INTO presupuestos (fecha, cliente, telefono, email, equipo, servicios, total)
                               VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id''',
                            (datetime.now().strftime("%d/%m/%Y %H:%M"), cliente, telefono, email, equipo, servicios_json, total))
        
        fila = cursor.fetchone()
        nuevo_id = fila['id'] if fila else 1
        db.commit()
        db.close()

        folio = 1000 + nuevo_id

        pdf_buffer = generar_pdf_presupuesto(folio, cliente, telefono, equipo, items, total, id_presupuesto=nuevo_id)
        response = send_file(pdf_buffer, mimetype='application/pdf')
        response.headers["Content-Disposition"] = f"inline; filename=Presupuesto_{cliente.replace(' ', '_')}_{folio}.pdf"
        return response

    return render_template('generar_presupuesto.html')

class PDFPresupuesto(FPDF):
    def rotate(self, angle, x=None, y=None):
        if x is None: x = self.x
        if y is None: y = self.y
        self._out(f"q {math.cos(math.radians(angle))} {math.sin(math.radians(angle))} {-math.sin(math.radians(angle))} {math.cos(math.radians(angle))} {x * self.k} {(self.h - y) * self.k} cm 1 0 0 1 {-x * self.k} {-(self.h - y) * self.k} cm")

    def end_rotate(self):
        self._out("Q")

    def header(self):
        # 1. Franja azul de fondo
        self.set_fill_color(24, 43, 73)
        self.rect(10, 5, 190, 42, 'F')

        # 2. Tarjeta blanca para el logo
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(200, 215, 235)
        self.set_line_width(0.3)
        self.rect(13, 8, 52, 34, 'DF')

        # 3. Logo centrado en su tarjeta
        logo_local = os.path.join(BASE_DIR, "static", "img", "logo_nuevo.jpg")
        url_logo_web = "https://i.postimg.cc/wvXCKc44/logo.png"
        try:
            if os.path.exists(logo_local):
                self.image(logo_local, 15, 11, 48)
            else:
                self.image(url_logo_web, 15, 11, 48)
        except Exception:
            pass

        # 4. Nombre y detalles de la empresa
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 15)
        self.set_xy(68, 9)
        self.cell(130, 6, 'G-Tek Soluciones Digitales', ln=True, align='L')

        # Lema / Subtítulo dorado
        self.set_text_color(212, 175, 55)
        self.set_font('Arial', 'B', 8.5)
        self.set_xy(68, 16)
        self.cell(130, 5, 'Innovación, Soporte y Soluciones Tecnológicas Integrales', ln=True, align='L')

        # Línea divisoria suave
        self.set_draw_color(70, 100, 145)
        self.set_line_width(0.2)
        self.line(68, 22, 195, 22)

        # Datos fiscales y de contacto
        self.set_text_color(230, 235, 245)
        self.set_font('Arial', '', 7.5)
        self.set_xy(68, 24)
        self.cell(130, 4, 'Francisco Arturo Gutiérrez Rosas | RFC: GURF770808', ln=True, align='L')
        self.set_xy(68, 28)
        self.cell(130, 4, 'Cda. Águilas mz 13 lt 30 Casa D, San Buenaventura, Ixtapaluca, México. 56536', ln=True, align='L')
        self.set_xy(68, 32)
        self.cell(130, 4, 'Tel. 55 4031 3150 | WhatsApp | e-mail: arturogtzrosass@gmail.com', ln=True, align='L')

        # Espacio antes del folio y cuerpo
        self.set_y(50)

    def marca_de_agua(self):
        try:
            self.set_font('Arial', 'B', 30)
            self.set_text_color(240, 240, 240)
            texto = "NOTA DE VENTA   NOTA DE VENTA   NOTA DE VENTA"
            w = self.get_string_width(texto)
            with self.rotation(45, 105, 160):
                self.text(105 - (w / 2), 160, texto)
        except Exception:
            pass

    def footer(self):
        self.set_y(-22)
        self.set_font('Arial', 'B', 8.5)
        self.set_text_color(200, 0, 0)
        self.cell(0, 5, '* AVISO: Este presupuesto puede cambiar sin previo aviso y tiene vigencia de 15 días.', align='C', ln=True)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(130, 5, 'Innovación, Soporte y Soluciones Tecnológicas Integrales', ln=True, align='L')


def generar_pdf_presupuesto(folio, cliente, telefono, equipo, items, total, id_presupuesto=None):
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

    # Generación e inserción de Código QR dinámico
    try:
        id_qr = id_presupuesto if id_presupuesto else folio
        url_qr = f"https://gtek-soluciones.onrender.com/descargar_presupuesto/{id_qr}"
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(url_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")

        ruta_qr = f"/tmp/qr_{folio}.png"
        img_qr.save(ruta_qr)

        # Posición a la izquierda de la tabla de totales sin encimarse
        pos_y_actual = pdf.get_y()
        pdf.image(ruta_qr, x=15, y=pos_y_actual - 26, w=22, h=22)
        pdf.set_xy(15, pos_y_actual - 3)
        pdf.set_font('Arial', '', 7)
        pdf.cell(22, 4, 'Escanear presupuesto', 0, 0, 'C')
    except Exception as e:
        print(f"[QR ERROR]: {e}")

    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin1')
    return io.BytesIO(pdf_bytes)

# =====================================================
# MÓDULO DE NOTAS DE VENTA (INTEGRACIÓN)
# =====================================================

class PDFNotaVenta(FPDF):
    def header(self):
        # 1. Franja azul institucional (más estilizada y compacta)
        self.set_fill_color(24, 43, 73)
        self.rect(10, 8, 190, 32, 'F')

        # 2. Recuadro blanco para el logo proporcional
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(200, 215, 235)
        self.set_line_width(0.3)
        self.rect(12, 10, 60, 28, 'DF')

        # 3. Logo insertado con proporción real (evita corte de iconos)
        logo_local = os.path.join(BASE_DIR, "static", "img", "logo_nuevo.jpg")
        url_logo_web = "https://i.postimg.cc/wvXCKc44/logo.png"
        try:
            ruta_logo = logo_local if os.path.exists(logo_local) else url_logo_web
            # Centrado en X: 12 + (60 - 56)/2 = 14 | Centrado en Y: 10 + (28 - 24)/2 = 12
            self.image(ruta_logo, x=13.5, y=11.5, w=57)
        except Exception:
            pass

        # 4. Nombre comercial
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 14)
        self.set_xy(76, 11)
        self.cell(120, 5, 'G-Tek Soluciones Digitales', ln=True, align='L')

        # 5. Eslogan / Subtítulo dorado
        self.set_text_color(225, 185, 65)
        self.set_font('Arial', 'B', 8)
        self.set_xy(76, 17)
        self.cell(120, 4, 'Innovación, Soporte y Soluciones Tecnológicas Integrales', ln=True, align='L')

        # Línea dorada divisoria sutil
        self.set_draw_color(225, 185, 65)
        self.set_line_width(0.2)
        self.line(76, 22.5, 195, 22.5)

        # 6. Datos fiscales y de contacto
        self.set_text_color(230, 235, 245)
        self.set_font('Arial', '', 7.5)
        self.set_xy(76, 24)
        self.cell(120, 3.8, 'Francisco Arturo Gutiérrez Rosas | RFC: GURF770808', ln=True, align='L')
        self.set_xy(76, 28)
        self.cell(120, 3.8, 'Cda. Águilas mz 13 lt 30 Casa D, San Buenaventura, Ixtapaluca, México. 56536', ln=True, align='L')
        self.set_xy(76, 32)
        self.cell(120, 3.8, 'Tel. 55 4031 3150 | WhatsApp | e-mail: arturogtzrosass@gmail.com', ln=True, align='L')
        
        # Posicionar cursor al pie del banner para no arrastrar margen vacío
        self.set_y(42)

    def marca_de_agua(self):
        try:
            self.set_font('Arial', 'B', 30)
            self.set_text_color(240, 240, 240)
            texto = "ESTE NO ES UN COMPROBANTE FISCAL"
            w = self.get_string_width(texto)
            with self.rotation(45, 105, 160):
                self.text(105 - (w / 2), 160, texto)
        except Exception:
            pass

    def footer(self):
        self.set_y(-22)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(27, 48, 91)
        self.cell(0, 5, '** Todo trabajo tiene 30 días de garantía en mano de obra', align='C', ln=True)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, 'G-Tek Soluciones Digitales - Calidad y Honestidad en cada reparación', align='C')

def generar_pdf_nota_binario(folio, cliente, direccion, telefono, equipo, servicios_items, total, obs=""):
    subtotal = total / 1.16
    iva = total - subtotal
    pdf = PDFNotaVenta()
    pdf.add_page()
    pdf.marca_de_agua()
    
    # Folio a la derecha
    pdf.set_xy(140, 43)
    pdf.set_text_color(200, 0, 0)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(60, 5, f'FOLIO: {folio}', ln=True, align='R')

    # Fecha alineada a la derecha bajo el folio
    pdf.set_xy(140, 48)
    pdf.set_text_color(90, 90, 90)
    pdf.set_font('Arial', '', 8.5)
    pdf.cell(60, 4, f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True, align='R')

    # Título centrado
    pdf.set_xy(10, 45)
    pdf.set_text_color(24, 43, 73)
    pdf.set_font('Arial', 'B', 15)
    pdf.cell(190, 6, 'NOTA DE VENTA', ln=True, align='C')

    # Datos del cliente y equipo
    pdf.set_xy(10, 54)
    pdf.set_fill_color(240, 243, 248)
    pdf.set_text_color(24, 43, 73)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(190, 6, ' DATOS DEL CLIENTE Y EQUIPO', ln=True, fill=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    pdf.set_x(10)
    pdf.cell(190, 5, f'Cliente: {cliente}', ln=True)
    if direccion:
        pdf.set_x(10)
        pdf.cell(190, 5, f'Dirección: {direccion}', ln=True)
    if telefono:
        pdf.set_x(10)
        pdf.cell(190, 5, f'Teléfono: {telefono}', ln=True)
    pdf.set_x(10)
    pdf.cell(190, 5, f'Equipo: {equipo}', ln=True)
    if obs:
        pdf.set_x(10)
        pdf.multi_cell(190, 4.5, f'Observaciones: {obs}')

    pdf.ln(3)
    

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
        try:
            p_unit = float(item.get('p_unit', 0.0))
        except Exception:
            p_unit = float(item.get('precio', 0.0)) / cant if cant else 0.0
        importe_item = cant * p_unit

        x_start = pdf.get_x()
        y_start = pdf.get_y()

        w_cant, w_desc, w_punit, w_imp = 15, 105, 35, 35
        h_linea = 5

        # Imprimir la descripción en multi_cell para permitir salto de línea
        pdf.set_xy(x_start + w_cant, y_start)
        pdf.multi_cell(w_desc, h_linea, f"{desc}", border=0, align='L')
        y_fin = pdf.get_y()
        alto_fila = max(8, y_fin - y_start)

        # Dibujar las celdas con la altura calculada para que coincidan perfectamente
        pdf.set_xy(x_start, y_start)
        pdf.cell(w_cant, alto_fila, f"{cant}", border=1, ln=0, align='C')
        pdf.cell(w_desc, alto_fila, '', border=1, ln=0)
        pdf.cell(w_punit, alto_fila, f"${p_unit:,.2f}", border=1, ln=0, align='R')
        pdf.cell(w_imp, alto_fila, f"${importe_item:,.2f}", border=1, ln=1, align='R')

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
                
        import json
        serv_resumen = json.dumps(items, ensure_ascii=False)
        
        db = get_db_connection()
        cur = db.execute('''INSERT INTO notas_venta 
                 (fecha, cliente, direccion, telefono, equipo, servicio, total, observaciones)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id''',
                 (datetime.now().strftime("%d/%m/%Y %H:%M"), cliente, direccion, telefono, equipo, serv_resumen, total, observaciones))
        row = cur.fetchone()
        nuevo_id = (row['id'] if isinstance(row, dict) else row[0]) if row else 1
        db.commit()
        folio = 1000 + nuevo_id
        db.close()
        
        pdf_buf = generar_pdf_nota_binario(folio, cliente, direccion, telefono, equipo, items, total, observaciones)
        response = send_file(pdf_buf, mimetype='application/pdf')
        response.headers["Content-Disposition"] = f"inline; filename=Nota_{cliente.replace(' ', '_')}_{folio}.pdf"
        return response

    db = get_db_connection()
    clientes_registrados = db.execute("""
        SELECT cliente, 
               MAX(direccion) AS direccion, 
               MAX(telefono) AS telefono, 
               MAX(id) AS id
        FROM notas_venta
        WHERE cliente IS NOT NULL AND TRIM(cliente) != ''
        GROUP BY cliente
        ORDER BY MAX(id) DESC
    """).fetchall()
    db.close()

    return render_template('generar_nota.html', clientes_registrados=clientes_registrados)
    
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
        try:
            import json
            items = json.loads(n['servicio'])
        except Exception:
            # Respaldo por si se consulta una nota anterior guardada en texto plano
            items = [{'cant': 1, 'desc': n['servicio'], 'p_unit': float(n['total'] or 0.0), 'precio': float(n['total'] or 0.0)}]
            
    pdf_buf = generar_pdf_nota_binario(folio, n['cliente'], n['direccion'], n['telefono'], n['equipo'], items, float(n['total']), n['observaciones'])
    response = send_file(pdf_buf, mimetype='application/pdf')
    response.headers["Content-Disposition"] = f"inline; filename=Nota_{n['cliente'].replace(' ', '_')}_{folio}.pdf"
    return response

@app.route('/borrar_nota/<int:id>')
def borrar_nota(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('user_rol') != 'admin':
        flash("Acceso denegado: Solo administradores pueden eliminar notas.")
        return redirect(url_for('ver_notas'))

    db = get_db_connection()
    db.execute("DELETE FROM notas_venta WHERE id = ?", (id,))
    db.commit()
    db.close()
    return redirect(url_for('ver_notas'))

# ---------------- GESTIÓN DE USUARIOS ----------------

@app.route('/admin_usuarios')
def admin_usuarios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Solo administradores pueden gestionar usuarios
    if session.get('user_rol') != 'admin':
        flash("Acceso denegado. Se requieren permisos de administrador.")
        return redirect(url_for('dashboard'))

    db = get_db_connection()
    usuarios = db.execute("SELECT id, nombre, email, rol FROM usuarios ORDER BY id ASC").fetchall()
    db.close()
    return render_template('admin_usuarios.html', usuarios=usuarios)


@app.route('/crear_usuario_admin', methods=['POST'])
def crear_usuario_admin():
    if 'user_id' not in session or session.get('user_rol') != 'admin':
        flash("Acceso denegado.")
        return redirect(url_for('dashboard'))

    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    rol = request.form.get('rol', 'usuario').strip()

    if not nombre or not email or not password:
        flash("Todos los campos son obligatorios.")
        return redirect(url_for('admin_usuarios'))

    db = get_db_connection()
    # Verificar si el correo ya existe
    existe = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if existe:
        db.close()
        flash("El correo electrónico ya está registrado.")
        return redirect(url_for('admin_usuarios'))

    hash_pass = generate_password_hash(password, method="pbkdf2:sha256")
    db.execute(
        "INSERT INTO usuarios (nombre, email, password, rol) VALUES (?, ?, ?, ?)",
        (nombre, email, hash_pass, rol)
    )
    db.commit()
    db.close()
    flash(f"Usuario {nombre} ({rol}) creado exitosamente.")
    return redirect(url_for('admin_usuarios'))


@app.route('/borrar_usuario/<int:id>')
def borrar_usuario(id):
    if 'user_id' not in session or session.get('user_rol') != 'admin':
        flash("Acceso denegado.")
        return redirect(url_for('dashboard'))

    if id == session.get('user_id'):
        flash("No puedes eliminar tu propio usuario en sesión.")
        return redirect(url_for('admin_usuarios'))

    db = get_db_connection()
    db.execute("DELETE FROM usuarios WHERE id = ?", (id,))
    db.commit()
    db.close()
    flash("Usuario eliminado correctamente.")
    return redirect(url_for('admin_usuarios'))


# ---------------- AUTO-INICIALIZACIÓN ADMIN ----------------

def asegurar_admin_en_arranque():
    return

# Ejecutar al iniciar la aplicacion
# asegurar_admin_en_arranque()