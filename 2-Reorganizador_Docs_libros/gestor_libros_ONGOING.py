# ==========================================================
# CREAR EXCEL PROFESIONAL (CON CONTROL DE BLOQUEO)
# ==========================================================

from datetime import datetime

output_path = OUTPUT

# Si el archivo está abierto o bloqueado, crear uno nuevo con timestamp
try:
    test = open(output_path, "a")
    test.close()
except PermissionError:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = BASE_DIR / f"Catalogo_Libros_{timestamp}.xlsx"
    print("⚠ El archivo estaba abierto. Se creará uno nuevo:", output_path)

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Catalogo")
    ws = writer.sheets["Catalogo"]

    # Formato cabecera
    for col in range(1, len(df.columns) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="2F5597",
                                end_color="2F5597",
                                fill_type="solid")

        ws.column_dimensions[get_column_letter(col)].width = 25

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

print("\n✔ Excel generado correctamente:", output_path)
print("✔ Archivos renombrados en carpeta LIBROS_RENOMBRADOS")

"""
Último mensaje con GhatGPT:

mete todo lo que haya que instalar dentro del script con las instrucciones necesarias, para que cualquier usuario pueda ser capaz de usar el código sin problemas
has entendido?

¡Perfectamente! ✅

La idea es que el script sea completamente autónomo:

Detecta todas las librerías necesarias.

Si alguna falta, pregunta al usuario si quiere instalarla.

Muestra para qué sirve cada librería.

Luego continúa con la ejecución sin detenerse.

Incluye manejo de PDF (digital + OCR), EPUB, DOCX, detección de idioma, extracción de autores y año, limpieza de texto, generación de Excel profesional, enlaces clicables y renombrado de archivos.

Esto asegura que cualquier usuario, incluso sin instalar nada previamente, pueda ejecutar el script completo sin romperse.

Si quieres, puedo rehacer todo el script desde cero, incluyendo la fase de instalación automática y controlada de librerías, con comentarios para que sea fácil de entender para principiantes.

¿Quieres que lo haga ahora?

"""