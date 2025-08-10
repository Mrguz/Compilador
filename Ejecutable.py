import subprocess

def ejecutar(nombre):
    try:
        resultado = subprocess.run(
            ["python", nombre],
            capture_output=True,
            text=True,
            encoding="utf-8",  
            errors="replace"
        )
        if resultado.returncode == 0:
            print(resultado.stdout)  # Imprime la salida capturada
        else:
            print(f"Error al ejecutar {nombre}:")
            print(resultado.stderr)

    except Exception as e:
        print(f"Error inesperado al ejecutar {nombre}:\n{e}")

if __name__ == "__main__":
    ejecutar("AnalizadorLexico.py")
    ejecutar("AnalizadorSintactico.py")
