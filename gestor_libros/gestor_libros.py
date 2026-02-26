# ==========================================================
# GESTOR DE LIBROS - VERSION ROBUSTA
# ==========================================================
# Este programa:
# - Verifica dependencias antes de usarlas
# - Crea LIBROS_RAW si no existe (con permiso)
# - Analiza PDF, EPUB, DOCX y TXT
# - Detecta idioma automáticamente
# - Extrae metadatos básicos
# - Genera CSV
# - Permite renombrar archivos en nueva carpeta
# ==========================================================

import os
import sys
import subprocess
import re
import shutil
from pathlib import Path

# ==========================================================
# 1️⃣ VERIFICACIÓN E INSTALACIÓN DE LIBRERÍAS
# ==========================================================

LIBRERIAS_NECESARIAS = [
    "pandas",
    "langdetect",
    "PyPDF2",
    "ebooklib",
    "beautifulsoup4",
    "python-docx"
]

def verificar_librerias():
    """
    Comprueba si las librerías necesarias están instaladas.
    Si falta alguna, pregunta si se desea instalar.
    """
    faltantes = []

    for lib in LIBRERIAS_NECESARIAS:
        try:
            __import__(lib.replace("-", "_"))
        except ImportError:
            faltantes.append(lib)

    if faltantes:
        print("\n⚠️ Faltan las siguientes librerías:")
        for f in faltantes:
            print(" -", f)

        instalar = input("\n¿Quieres instalarlas ahora? (s/n): ").lower()

        if instalar == "s":
            for lib in faltantes:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            print("\n✅ Librerías instaladas. Reinicia el programa.")
            sys.exit()
        else:
            print("❌ No se puede continuar sin instalar dependencias.")
            sys.exit()

verificar_librerias()

# ==========================================================
# 2️⃣ IMPORTACIONES (ahora seguras)
# ==========================================================

import pandas as pd
from langdetect import detect
from PyPDF2 import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup
import docx

# ==========================================================
# CONFIGURACIÓN DE RUTAS
# ==========================================================

BASE_DIR = Path(__file__).parent
RAW_FOLDER = BASE_DIR / "LIBROS_RAW"
OUTPUT_CSV = BASE_DIR / "catalogo_libros.csv"
RENAMED_FOLDER = BASE_DIR / "LIBROS_RENOMBRADOS"

# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def comprobar_carpeta():
    """
    Comprueba si existe LIBROS_RAW.
    Si no existe, pide permiso para crearla.
    """
    if not RAW_FOLDER.exists():
        print("⚠️ La carpeta LIBROS_RAW no existe.")
        crear = input("¿Quieres crearla? (s/n): ").lower()

        if crear == "s":
            RAW_FOLDER.mkdir()
            print("✅ Carpeta creada.")
            print("📂 Añade los libros dentro y vuelve a ejecutar.")
            sys.exit()
        else:
            print("❌ No se puede continuar.")
            sys.exit()

def limpiar_texto(texto):
    if not texto:
        return ""
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def formatear_autores(lista_autores):
    """
    - Más de 3 autores → VVAA
    - 2 o 3 → separados por /
    """
    if not lista_autores:
        return "Desconocido"

    if len(lista_autores) > 3:
        return "VVAA"

    return " / ".join(lista_autores)

def detectar_idioma(texto):
    """
    Detecta idioma automáticamente.
    """
    try:
        return detect(texto[:1000])
    except:
        return "Desconocido"

def extraer_texto(ruta):
    extension = ruta.suffix.lower()
    texto = ""

    try:
        if extension == ".pdf":
            reader = PdfReader(ruta)
            for page in reader.pages[:5]:
                texto += page.extract_text() or ""

        elif extension == ".epub":
            book = epub.read_epub(ruta)
            for item in book.get_items():
                if item.get_type() == 9:
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    texto += soup.get_text()

        elif extension == ".docx":
            documento = docx.Document(ruta)
            for p in documento.paragraphs:
                texto += p.text + " "

        elif extension == ".txt":
            with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                texto = f.read()

    except Exception as e:
        print(f"⚠️ Error leyendo {ruta.name}: {e}")

    return limpiar_texto(texto)

def extraer_metadatos(ruta):
    texto = extraer_texto(ruta)

    titulo = ruta.stem
    autores = formatear_autores([])

    # Buscar año en el texto
    match = re.search(r"(19|20)\d{2}", texto)
    año = match.group() if match else "Desconocido"

    idioma = detectar_idioma(texto)

    palabras = texto.split()
    resumen = " ".join(palabras[:10]) if palabras else ""

    tamaño = round(ruta.stat().st_size / 1024, 2)
    ultima_mod = ruta.stat().st_mtime
    año_mod = pd.to_datetime(ultima_mod, unit="s").year

    return {
        "Nombre archivo": ruta.name,
        "Extensión": ruta.suffix,
        "Peso (KB)": tamaño,
        "Año última modificación": año_mod,
        "Título": titulo,
        "Autor": autores,
        "Año publicación": año,
        "Idioma detectado": idioma,
        "Resumen breve": resumen,
        "Ruta": str(ruta)
    }

def renombrar_archivos(df):
    if not RENAMED_FOLDER.exists():
        RENAMED_FOLDER.mkdir()

    for _, fila in df.iterrows():
        original = Path(fila["Ruta"])

        nuevo_nombre = f"{fila['Autor']} [{fila['Año publicación']}] {fila['Título']}{original.suffix}"
        nuevo_nombre = re.sub(r'[<>:"/\\|?*]', "", nuevo_nombre)

        destino = RENAMED_FOLDER / nuevo_nombre

        try:
            shutil.copy2(original, destino)
        except Exception as e:
            print("Error copiando:", e)

    print("✅ Archivos renombrados guardados en LIBROS_RENOMBRADOS")

# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

def main():
    comprobar_carpeta()

    archivos = list(RAW_FOLDER.glob("*.*"))

    if not archivos:
        print("⚠️ No hay archivos en LIBROS_RAW.")
        return

    datos = []

    print("\n🔍 Analizando documentos...\n")

    for archivo in archivos:
        print("Procesando:", archivo.name)
        datos.append(extraer_metadatos(archivo))

    df = pd.DataFrame(datos)
    df.to_csv(OUTPUT_CSV, index=False)

    print("\n✅ Catálogo generado:", OUTPUT_CSV)

    opcion = input("\n¿Quieres crear carpeta con archivos renombrados? (s/n): ").lower()

    if opcion == "s":
        renombrar_archivos(df)

# ==========================================================

if __name__ == "__main__":
    main()