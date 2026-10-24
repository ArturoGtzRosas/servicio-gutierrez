import os
from datetime import datetime

if __name__ == '__main__':
    # Limpiar pantalla (funciona en Windows)
    os.system('cls')

    print("--- GENERADOR DE COTIZACION: SERVICIO GUTIERREZ ---")

    # Datos del servicio
    cliente = input("Nombre del cliente: ")
    descripcion = input("Descripcion del trabajo: ")
    costo_piezas = float(input("Costo total de refacciones: $"))
    mano_de_obra = float(input("Costo de mano de obra: $"))

    total = costo_piezas + mano_de_obra
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Diseño del recibo
    recibo = f"""
========================================
       G-Tek Soluciones Digitales - COTIZACIÓN
========================================
FECHA:      {fecha_actual}
CLIENTE:    {cliente}
TRABAJO:    {descripcion}
----------------------------------------
Refacciones:      ${costo_piezas:,.2f}
Mano de obra:     ${mano_de_obra:,.2f}
----------------------------------------
TOTAL ESTIMADO:   ${total:,.2f}
========================================
"""

    print(recibo)

    # Guardar en el historial
    try:
        with open("historial_ventas.txt", "a", encoding="utf-8") as archivo:
            archivo.write(recibo + "\n")
        print(">>> Presupuesto guardado en 'historial_ventas.txt'")
    except Exception as e:
        print(f"No se pudo guardar: {e}")