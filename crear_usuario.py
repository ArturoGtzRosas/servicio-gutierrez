from werkzeug.security import generate_password_hash
import mysql.connector

try:
    print("--- Intentando conectar con la base de datos ---")
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="", 
        database="servicio_gutierrez"
    )
    cursor = db.cursor()

    print("--- Generando contraseña encriptada ---")
    # Usamos pbkdf2:sha256 para que sea compatible con tu Python 3.8
    password_encriptada = generate_password_hash("admin123", method='pbkdf2:sha256')

    print("--- Insertando al usuario Arturo ---")
    sql = "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)"
    valores = ("Arturo", "arturo@servicio.com", password_encriptada)
    
    cursor.execute(sql, valores)
    db.commit()

    print("✅ ¡EXITO TOTAL! El usuario ha sido creado.")
    print("Email: arturo@servicio.com")
    print("Password: admin123")

except mysql.connector.Error as err:
    print(f"❌ Error de MySQL: {err}")
except Exception as e:
    print(f"❌ Error de Python: {e}")
finally:
    # Esta parte cierra la conexión de forma segura
    if 'db' in locals() and db.is_connected():
        cursor.close()
        db.close()
        print("--- Conexión cerrada correctamente ---")