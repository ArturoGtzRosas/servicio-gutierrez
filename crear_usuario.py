import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "servicio_gutierrez.db"

def inicializar_admin():
    print("--- Conectando a SQLite ---")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Crear tabla usuarios si no existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # 2. Generar contraseña encriptada
    password_hash = generate_password_hash("admin123")

    # 3. Insertar o actualizar el usuario administrador
    cursor.execute("""
    INSERT INTO usuarios (nombre, email, password)
    VALUES (?, ?, ?)
    ON CONFLICT(email) DO UPDATE SET password=excluded.password
    """, ("Arturo", "arturo@servicio.com", password_hash))

    conn.commit()
    conn.close()
    print("✅ Tabla creada y usuario 'arturo@servicio.com' listo con password 'admin123'")

if __name__ == "__main__":
    inicializar_admin()