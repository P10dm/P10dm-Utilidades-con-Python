# -*- coding: utf-8 -*-
"""
Transformador de notebooks Jupyter a Python (.py) con manejo de librerías
-----------------------------------------------------------------------
1️⃣ Detecta librerías necesarias en los notebooks.
2️⃣ Traduce nombres problemáticos a paquetes pip correctos.
3️⃣ Pregunta si se desean instalar librerías faltantes.
4️⃣ Convierte notebooks a scripts .py respetando comentarios Markdown.
5️⃣ Genera un Excel con links a todos los archivos .py.
"""

import os
import re
import subprocess
import sys

# ---------------------------
# Función para instalar paquetes correctamente con mapeos
# ---------------------------
def install_package(pkg_name):
    """Instala un paquete usando pip con mapeo de nombres problemáticos"""
    name_mapping = {
        "sklearn": "scikit-learn",
        "cv2": "opencv-python",
        "PIL": "Pillow"
        # Puedes añadir aquí más mapeos si detectas paquetes problemáticos
    }
    pip_name = name_mapping.get(pkg_name, pkg_name)
    print(f"Instalando {pip_name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

# ---------------------------
# Funciones para detectar imports en código
# ---------------------------
def extract_imports_from_code(code_lines):
    """Detecta librerías importadas en líneas de código y devuelve un set con los nombres"""
    imports = set()
    pattern = re.compile(r'^\s*(?:import\s+(\S+)|from\s+(\S+)\s+import\s+)')
    for line in code_lines:
        match = pattern.match(line)
        if match:
            lib = match.group(1) or match.group(2)
            lib = lib.split('.')[0]
            imports.add(lib)
    return imports

def gather_imports_from_notebook(nb_path):
    """Lee un notebook y devuelve un set de librerías usadas en sus celdas de código"""
    import nbformat
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    code_lines = []
    for cell in nb.cells:
        if cell.cell_type == "code":
            code_lines.extend(cell.source.splitlines())
    return extract_imports_from_code(code_lines)

# ---------------------------
# Función para instalar librerías faltantes
# ---------------------------
def install_missing_libraries(libs):
    """Instala librerías faltantes preguntando al usuario"""
    missing = []
    for lib in libs:
        try:
            __import__(lib)
        except ModuleNotFoundError:
            missing.append(lib)

    if missing:
        print("\nLas siguientes librerías faltan:")
        print(", ".join(missing))
        answer = input("¿Deseas instalarlas ahora? (s/n): ").strip().lower()
        if answer == "s":
            for lib in missing:
                try:
                    install_package(lib)
                except subprocess.CalledProcessError:
                    print(f"[ERROR] No se pudo instalar {lib}. Revisa el nombre o tu conexión a internet.")
            print("\n✅ Instalación completada.\n")
        else:
            print("\n⚠️ Algunas librerías pueden faltar y los scripts .py pueden fallar.\n")
    else:
        print("\n✅ Todas las librerías necesarias están instaladas.\n")

# ---------------------------
# Función para convertir notebook a .py
# ---------------------------
def convert_notebook(nb_path, input_folder, output_folder):
    import nbformat
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    py_lines = []

    for cell in nb.cells:
        if cell.cell_type == "markdown":
            for line in cell.source.splitlines():
                py_lines.append("# " + line)
            py_lines.append("")
        elif cell.cell_type == "code":
            if "application/octet-stream" in str(cell.get("outputs", "")):
                py_lines.append("# [SALTEADO] Celda binaria no procesable")
                py_lines.append("")
                continue
            for line in cell.source.splitlines():
                py_lines.append(line)
            py_lines.append("")

    # Crear estructura de carpetas en la salida
    relative_path = os.path.relpath(nb_path, input_folder)
    relative_dir = os.path.dirname(relative_path)
    final_output_dir = os.path.join(output_folder, relative_dir)
    os.makedirs(final_output_dir, exist_ok=True)

    filename = os.path.splitext(os.path.basename(nb_path))[0] + ".py"
    py_path = os.path.join(final_output_dir, filename)
    with open(py_path, "w", encoding="utf-8") as f:
        f.write("\n".join(py_lines))

    return py_path

# ---------------------------
# Crear Excel con links
# ---------------------------
def create_excel_file(py_files, output_folder):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Scripts Python"
    ws.append(["Archivo", "Ruta completa"])
    for py in py_files:
        ws.append([os.path.basename(py), py])
    excel_path = os.path.join(output_folder, "Lista_Py_Files.xlsx")
    wb.save(excel_path)
    print(f"\n✅ Excel creado con links a los archivos .py: {excel_path}")

# ---------------------------
# Función principal
# ---------------------------
def main():
    input_folder = input("Ruta de la carpeta con notebooks (.ipynb):\n").strip()
    input_folder = os.path.abspath(input_folder)
    if not os.path.exists(input_folder):
        print("[ERROR] La carpeta de entrada no existe.")
        return

    output_folder = input("Ruta de la carpeta de salida para los archivos .py:\n").strip()
    output_folder = os.path.abspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    # Detectar notebooks y librerías
    notebooks = []
    all_libs = set()
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith(".ipynb"):
                nb_path = os.path.join(root, file)
                notebooks.append(nb_path)
                all_libs.update(gather_imports_from_notebook(nb_path))

    print(f"\nSe encontraron {len(notebooks)} notebooks.")
    print("Librerías detectadas:")
    print(", ".join(sorted(all_libs)))

    # Instalar librerías faltantes con mapeo
    install_missing_libraries(all_libs)

    # Confirmar transformación
    cont = input("¿Deseas continuar con la transformación a .py? (s/n): ").strip().lower()
    if cont != "s":
        print("Transformación cancelada.")
        return

    # Transformar notebooks
    py_files = []
    for nb in notebooks:
        py_path = convert_notebook(nb, input_folder, output_folder)
        py_files.append(py_path)
        print(f"[OK] {nb} → {py_path}")

    # Crear Excel con links
    create_excel_file(py_files, output_folder)

    print("\n🎉 ¡Transformación completada!")

# ---------------------------
if __name__ == "__main__":
    main()