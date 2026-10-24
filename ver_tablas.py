import sqlite3

conn = sqlite3.connect("servicio_gutierrez.db")
cursor = conn.cursor()

# Consultar nombres de tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tablas = [fila[0] for fila in cursor.fetchall()]
print("Tablas encontradas:", tablas)

# Ver cantidad de registros por tabla
for tabla in tablas:
    if tabla != "sqlite_sequence":
        cursor.execute(f"SELECT count(*) FROM {tabla}")
        total = cursor.fetchone()[0]
        print(f" - {tabla}: {total} registros")

conn.close()