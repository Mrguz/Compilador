from ply import lex
import os

# Palabras reservadas del lenguaje TigerScript
reserved = {
    'Inicio': 'PALABRA_RESERVADA_INICIO',
    'Fin': 'PALABRA_RESERVADA_FIN',
    'ImprimirNumero': 'PALABRA_RESERVADA_IMPRIMIR_NUMERO',
    'ImprimirCadena': 'PALABRA_RESERVADA_IMPRIMIR_CADENA',
    'ImprimirBoleano': 'PALABRA_RESERVADA_IMPRIMIR_BOLEANO',
    'LeerNumero': 'PALABRA_RESERVADA_LEER_NUMERO',
    'LeerCadena': 'PALABRA_RESERVADA_LEER_CADENA',
    'LeerBoleano': 'PALABRA_RESERVADA_LEER_BOLEANO',
    'Si': 'PALABRA_RESERVADA_SI',
    'Entonces': 'PALABRA_RESERVADA_ENTONCES',
    'Sino': 'PALABRA_RESERVADA_SINO',
    'Mientras': 'PALABRA_RESERVADA_MIENTRAS',
    'Hacer': 'PALABRA_RESERVADA_HACER',
    'Verdadero': 'PALABRA_RESERVADA_VERDADERO',
    'Falso': 'PALABRA_RESERVADA_FALSO'
}

# Tipos de datos
tipos_dato = {
    'Cadena': 'TIPO_DATO',
    'Entero': 'TIPO_DATO',
    'Boleano': 'TIPO_DATO'
}

tokens = [
    'PROGRAMA',
    'IDENTIFICADOR',
    'CONSTANTE',
    'TEXTO',
    'PAREN_IZQ',
    'PAREN_DER',
    'SUMA',
    'RESTA',
    'MULTIPLICACION',
    'DIVISION',
    'IGUAL',
    'ERROR_IDENTIFICADOR',
    'ERROR_IDENTIFICADOR_NUM',
] + list(reserved.values()) + list(set(tipos_dato.values()))

errores_lexicos = []

# Símbolos simples
t_IGUAL = r'='
t_PAREN_IZQ = r'\('
t_PAREN_DER = r'\)'
t_SUMA = r'\+'
t_RESTA = r'-'
t_MULTIPLICACION = r'\*'
t_DIVISION = r'/'

# Comentarios: ignorar
def t_COMENTARIO(t):
    r'--.*'
    pass

# Texto entre comillas dobles
def t_TEXTO(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1]  # eliminar comillas
    return t

# Palabra clave del programa
def t_PROGRAMA(t):
    r'TigerScript'
    return t

# Errores por comenzar con un número seguido de letras (ej: 12abc)
def t_ERROR_IDENTIFICADOR_NUM(t):
    r'\d+[a-zA-Z_]+[a-zA-Z0-9_]*'
    errores_lexicos.append({
        'line': t.lineno,
        'value': t.value,
        'type': 'ERROR_IDENTIFICADOR'
    })
    return t

# Errores por símbolos inválidos dentro del identificador (menos operadores válidos aislados)
def t_ERROR_IDENTIFICADOR(t):
    # Regex simplificada para no atrapar operadores aislados
    r'[a-zA-Z_][^\s"\'\(\)=+\-*/\d\n\t\r]*[^a-zA-Z0-9_\s"\'\(\)=+\-*/\n\t\r]+[^\s"\'\(\)=+\-*/\n\t\r]*'
    errores_lexicos.append({
        'line': t.lineno,
        'value': t.value,
        'type': 'ERROR_IDENTIFICADOR'
    })
    return t

# Errores por operadores dentro de identificadores (ej: var+name)
def t_ERROR_IDENTIFICADOR_MAL_FORMADO(t):
    r'[a-zA-Z_]+([+\-*/=]+[a-zA-Z0-9_]+)+'
    errores_lexicos.append({
        'line': t.lineno,
        'value': t.value,
        'type': 'ERROR_IDENTIFICADOR'
    })
    t.type = 'ERROR_IDENTIFICADOR'
    return t

# Errores por símbolos no permitidos al inicio o final de un identificador
def t_ERROR_IDENTIFICADOR_INICIO(t):
    r'([@]+[a-zA-Z_0-9]*|[a-zA-Z_0-9]+[@]+)'
    errores_lexicos.append({
        'line': t.lineno,
        'value': t.value,
        'type': 'ERROR_IDENTIFICADOR'
    })
    t.type = 'ERROR_IDENTIFICADOR'
    return t


# Identificador válido (con prioridad baja para no capturar errores primero)
def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value in reserved:
        t.type = reserved[t.value]
    elif t.value in tipos_dato:
        t.type = tipos_dato[t.value]
    return t

# Constante numérica (entera)
def t_CONSTANTE(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Ignorar espacios y tabs
t_ignore = ' \t'

# Contador de líneas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Error genérico para cualquier carácter no reconocido
def t_error(t):
    errores_lexicos.append({
        'line': t.lineno,
        'value': t.value[0],
        'type': 'ERROR_IDENTIFICADOR'
    })
    t.lexer.skip(1)

# Funciones para generar archivos de salida
def generar_archivo_tok(tokens_analizados):
    with open('progfte.tok', 'w', encoding='utf-8') as f:
        for token in tokens_analizados:
            if token['type'] != 'COMENTARIO':
                f.write(f"Renglón: {token['line']:<7} Lexema: {str(token['value']):<15} Token: {token['type']}\n")

def generar_archivo_tab(tokens_analizados):
    token_codes = {
        'PROGRAMA': 100,
        'TIPO_DATO': 200,
        'IDENTIFICADOR': 300,
        'CONSTANTE': 400,
        'PALABRA_RESERVADA_INICIO': 1,
        'PALABRA_RESERVADA_FIN': 2,
        'PALABRA_RESERVADA_IMPRIMIR_NUMERO': 10,
        'PALABRA_RESERVADA_IMPRIMIR_CADENA': 11,
        'PALABRA_RESERVADA_IMPRIMIR_BOLEANO': 12,
        'PAREN_IZQ': 50,
        'PAREN_DER': 51,
        'SUMA': 60,
        'RESTA': 61,
        'MULTIPLICACION': 62,
        'DIVISION': 63,
        'IGUAL': 70,
        'ERROR_IDENTIFICADOR': 0,
        'ERROR_IDENTIFICADOR_NUM': 0,
    }
    with open('progfte.tab', 'w', encoding='utf-8') as f:
        f.write("{:<8} {:<20} {:<50} {:<15}\n".format("No", "Lexema", "Token", "Referencia"))
        f.write("-"*95 + "\n")
        
        simbolos = []
        # Evitar duplicados en símbolos válidos
        for token in tokens_analizados:
            if token['type'] in ['IDENTIFICADOR', 'PROGRAMA', 'TIPO_DATO'] + list(reserved.values()):
                if not any(s['value'] == token['value'] and s['type'] == token['type'] for s in simbolos):
                    simbolos.append(token)

        # Agregar errores
        for error in errores_lexicos:
            simbolos.append({
                'value': error['value'],
                'type': error['type'],
                'line': error['line']
            })

        for i, simbolo in enumerate(simbolos, 1):
            f.write("{:<8} {:<20} {:<50} {:<15}\n".format(
                i,
                simbolo['value'],
                simbolo['type'],
                token_codes.get(simbolo['type'], 999)
            ))

def generar_depuracion(tokens_analizados):
    depurado = []
    i = 0
    n = len(tokens_analizados)
    while i < n:
        token = tokens_analizados[i]
        if token['type'] == 'COMENTARIO':
            i += 1
            continue
        # Agrupar asignaciones como token1=token2=token3...
        if (i+2 < n and
            tokens_analizados[i]['type'] == 'IDENTIFICADOR' and
            tokens_analizados[i+1]['type'] == 'IGUAL'):
            depurado.append(f"{token['value']}{tokens_analizados[i+1]['value']}{tokens_analizados[i+2]['value']}")
            i += 3
        else:
            depurado.append(str(token['value']))
            i += 1
    return ''.join(depurado)

def analizar_archivo(archivo_entrada):
    global errores_lexicos
    errores_lexicos = []
    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            contenido = f.readlines()
        if not contenido or not contenido[0].strip().startswith('TigerScript '):
            print("Error: La primera línea debe comenzar con 'TigerScript' seguido del nombre del archivo")
            return False

        lexer.input(''.join(contenido))
        tokens_analizados = []

        while True:
            tok = lexer.token()
            if not tok:
                break
            tokens_analizados.append({
                'type': tok.type,
                'value': tok.value,
                'line': tok.lineno
            })

        generar_archivo_tok(tokens_analizados)
        generar_archivo_tab(tokens_analizados)

        depuracion = generar_depuracion(tokens_analizados)
        with open('progfte.dep', 'w', encoding='utf-8') as f:
            f.write(depuracion)

        return True

    except Exception as e:
        print(f"Error durante el análisis: {e}")
        return False

lexer = lex.lex()

if __name__ == '__main__':
    archivo_entrada = 'progfte.txt'
    if os.path.exists(archivo_entrada):
        analizar_archivo(archivo_entrada)
    else:
        print(f"Error: No se encuentra el archivo '{archivo_entrada}'")
