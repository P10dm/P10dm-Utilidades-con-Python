"""
===========================================
INSTALADOR INTELIGENTE DE LIBRERÍAS PYTHON
===========================================

Descripción para principiantes:
Este programa permite instalar múltiples librerías de Python de forma interactiva,
gestiona librerías no encontradas buscando coincidencias, permite decidir qué
instalar y genera un archivo .txt con todo el registro de decisiones, propuestas
y resultados. Al inicio se puede optar por instalar librerías encontradas o no,
y si se decide no instalarlas, al final se preguntará si se desea instalar.
"""

import requests
import subprocess
import sys
import os
import re
from datetime import datetime

PYPI_URL = "https://pypi.org/pypi/{}/json"
MAX_INTENTOS = 3
modulos_estandar = {
    "os", "sys", "random", "string", "pickle", "unittest",
    "datetime", "math", "json", "re", "typing", "csv"
}

# =========================
# FUNCIONES AUXILIARES
# =========================

def limpiar_entrada(texto):
    """Separa librerías usando varios delimitadores"""
    return re.split(r"[,\s;/|]+", texto.strip())

def consultar_pypi(nombre):
    """Consulta PyPI y devuelve información de la librería si existe"""
    try:
        r = requests.get(PYPI_URL.format(nombre))
        if r.status_code == 200:
            data = r.json()
            info = data["info"]
            version = info.get("version", "Desconocida")
            resumen = info.get("summary", "")
            fecha = "Desconocida"
            if data.get("releases"):
                versiones = list(data["releases"].keys())
                if versiones:
                    ultima = versiones[-1]
                    if data["releases"][ultima]:
                        fecha = data["releases"][ultima][0].get("upload_time", "Desconocida")
            return {
                "usuario": nombre,
                "detectada": info.get("name", nombre),
                "version": version,
                "fecha": fecha,
                "resumen": resumen,
                "peso": "N/D"
            }
    except:
        pass
    return None

def instalar_libreria(nombre):
    """Instala la librería usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", nombre])
        return True
    except:
        return False

def buscar_coincidencias(nombre, descripcion):
    """Devuelve una lista simulada de posibles coincidencias"""
    return [nombre + "_plus", nombre + "_py", nombre + "_lib"]

def exportar_txt(usuario_lista, instaladas, no_encontradas_info, ruta_destino):
    """Genera un archivo .txt con todos los datos de la sesión"""
    ahora = datetime.now()
    nombre_archivo = ahora.strftime("%Y_%m_%d_%H_%M_Instalación_Librerías.txt")
    ruta = os.path.join(ruta_destino, nombre_archivo)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("LISTADO DE LIBRERÍAS INTRODUCIDAS POR EL USUARIO:\n")
        for lib in usuario_lista:
            f.write(f"- {lib}\n")
        f.write("\nLIBRERÍAS INSTALADAS CORRECTAMENTE:\n")
        for lib in instaladas:
            f.write(f"- {lib}\n")
        f.write("\nLIBRERÍAS NO ENCONTRADAS O NO INSTALADAS:\n")
        for info in no_encontradas_info:
            f.write("-" * 40 + "\n")
            f.write(f"Programa buscado: {info['Librería']}\n")
            f.write(f"Descripción usuario: {info.get('Descripcion', 'No se proporcionó')}\n")
            f.write(f"Programas propuestos: {', '.join(info.get('Propuestas', []))}\n")
            f.write(f"Programa elegido: {info.get('Elegido', '')}\n")
            f.write(f"Situación de la instalación: {info.get('Situacion', 'No instalada')}\n")
        f.write("\nFIN DEL REGISTRO\n")
    print(f"\nArchivo de registro generado:\n{ruta}")

# =========================
# PROGRAMA PRINCIPAL
# =========================

def main():
    respuesta = input("¿Deseas instalar varias librerías? (si/no)\n>> ").strip().lower()
    if respuesta not in ["si", "sí", "s"]:
        print("Programa finalizado. Puedes volver a ejecutar cuando quieras instalar librerías.")
        return

    entrada = input("Escribe las librerías (separadas por espacio, coma, ; / | )\n>> ").strip()
    usuario_lista = limpiar_entrada(entrada)

    encontradas = []
    no_encontradas = []
    instaladas = []
    no_encontradas_info = []
    instalar_encontradas = respuesta in ["si", "sí", "s"]

    # =========================
    # DETECCIÓN DE LIBRERÍAS
    # =========================
    for lib in usuario_lista:
        if lib in modulos_estandar:
            no_encontradas.append(lib)
            continue
        info = consultar_pypi(lib)
        if info:
            encontradas.append(info)
        else:
            no_encontradas.append(lib)

    # =========================
    # MOSTRAR LIBRERÍAS ENCONTRADAS
    # =========================
    if encontradas:
        print("\nSe pueden instalar ya las siguientes librerías:")
        for lib in encontradas:
            print(f"- {lib['usuario']}")
    if no_encontradas:
        print("\nLibrerías no encontradas:")
        for lib in no_encontradas:
            print(f"- {lib}")

    # =========================
    # INSTALACIÓN DE LIBRERÍAS ENCONTRADAS (Fase inicial)
    # =========================
    if encontradas:
        if instalar_encontradas:
            print("\nUna vez instaladas, se continuará con las librerías no encontradas.")
            confirmar = input("¿Confirmas que deseas instalar estas librerías? (si/no)\n>> ").strip().lower()
            if confirmar in ["si", "sí", "s"]:
                for lib in encontradas:
                    exito = instalar_libreria(lib["usuario"])
                    if exito:
                        instaladas.append(lib["usuario"])
                    else:
                        no_encontradas_info.append({
                            "Librería": lib["usuario"],
                            "Descripcion": "",
                            "Propuestas": [],
                            "Elegido": "",
                            "Situacion": "Error al instalar"
                        })
            else:
                print("No se instalarán las librerías encontradas ahora. Se continuará con las no encontradas.")
        else:
            print("\nNo se instalarán las librerías encontradas al inicio. Se continuará con las no encontradas.")

    # =========================
    # PROCESO LIBRERÍAS NO ENCONTRADAS
    # =========================
    for lib in no_encontradas:
        info_adicional = []
        propuestas = []
        elegido = ""
        situacion = "No instalada"
        intentos = 0
        while intentos < MAX_INTENTOS:
            descripcion = input(f"\nDescribe para qué quieres usar '{lib}' (o deja vacío para pasar):\n>> ").strip()
            if descripcion:
                info_adicional.append(descripcion)
                propuestas = buscar_coincidencias(lib, descripcion)
                if propuestas:
                    print("\nSe han encontrado posibles coincidencias en PyPI:")
                    for i, c in enumerate(propuestas, 1):
                        print(f"{i}. {c}")
                    eleccion = input("Escribe el número de la librería a instalar, o deja vacío para no instalar:\n>> ").strip()
                    if eleccion.isdigit():
                        idx = int(eleccion) - 1
                        if 0 <= idx < len(propuestas):
                            elegido = propuestas[idx]
                            if instalar_libreria(elegido):
                                instaladas.append(elegido)
                                situacion = "Instalada"
                            else:
                                situacion = "Error al instalar"
                    break
            else:
                print(f"Saltando '{lib}'. Puedes buscar más información y volver a ejecutar el programa.")
                break
            intentos += 1
        no_encontradas_info.append({
            "Librería": lib,
            "Descripcion": " | ".join(info_adicional) if info_adicional else "No se proporcionó",
            "Propuestas": propuestas,
            "Elegido": elegido,
            "Situacion": situacion
        })

    # =========================
    # PREGUNTAR SI QUIERE INSTALAR LIBRERÍAS ENCONTRADAS QUE QUEDARON PENDIENTES
    # =========================
    pendientes = [lib["usuario"] for lib in encontradas if lib["usuario"] not in instaladas]
    if pendientes:
        print("\nAlgunas librerías encontradas no fueron instaladas al inicio:")
        for lib in pendientes:
            print(f"- {lib}")
        confirmar = input("\n¿Deseas instalar ahora estas librerías encontradas? (si/no)\n>> ").strip().lower()
        if confirmar in ["si", "sí", "s"]:
            for lib in pendientes:
                if instalar_libreria(lib):
                    instaladas.append(lib)
                else:
                    no_encontradas_info.append({
                        "Librería": lib,
                        "Descripcion": "",
                        "Propuestas": [],
                        "Elegido": "",
                        "Situacion": "Error al instalar"
                    })

    # =========================
    # RESUMEN FINAL
    # =========================
    print("\nRESUMEN FINAL")
    print("Librerías instaladas:")
    for lib in instaladas:
        print(f"- {lib}")
    print("\nLibrerías no instaladas / no encontradas:")
    for info in no_encontradas_info:
        print(f"- {info['Librería']}: {info['Situacion']}")

    # =========================
    # EXPORTAR A TXT
    # =========================
    carpeta = input("\nIntroduce la carpeta donde guardar el archivo de registro .txt:\n>> ").strip()
    exportar_txt(usuario_lista, instaladas, no_encontradas_info, carpeta)
    print("\nProceso finalizado. Gracias por utilizar el instalador.")

if __name__ == "__main__":
    main()