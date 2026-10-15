import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "servicio_gutierrez.db"

def inicializar_admin():
    print("--- Conectando a SQLite ---")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Crear tabla usuarios si no existe (incluyendo rol)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol TEXT DEFAULT 'usuario'
    )
    """)

    # 2. Si la tabla ya existía sin la columna 'rol', la agregamos
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT DEFAULT 'usuario'")
        print("-> Columna 'rol' agregada a la tabla usuarios.")
    except sqlite3.OperationalError:
        pass  # Ya existe la columna

    # 3. Generar contraseña encriptada
    password_hash = generate_password_hash("admin123", method="pbkdf2:sha256")

    # 4. Insertar o actualizar usuario como administrador
    cursor.execute("""
    INSERT INTO usuarios (nombre, email, password, rol)
    VALUES (?, ?, ?, 'admin')
    ON CONFLICT(email) DO UPDATE SET password=excluded.password, rol='admin'
    """, ("Arturo", "arturo@servicio.com", password_hash))

    conn.commit()
    conn.close()
    print("✅ Usuario 'arturo@servicio.com' listo con rol 'admin'.")

if __name__ == "__main__":
    inicializar_admin()