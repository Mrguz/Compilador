import tkinter as tk
from tkinter import scrolledtext
import re
import os

# Diccionario de Precedencia (Jerarquía de Operadores)
# Es esencial para el Algoritmo Shunting-yard y la correcta generación de cuádruplos.
# Los valores más altos indican mayor precedencia (Ej: '*' y '/' antes que '+' y '-').
PREDECENCIA = {
    '+': 1, '-': 1,
    '*': 2, '/': 2,
    '(': 0 
}

class GeneradorTemporales:
    """
    CLASE DE SOPORTE PARA CÓDIGO INTERMEDIO (CUÁDRUPLOS)
    
    Propósito:
        Generar identificadores únicos para variables temporales (T1, T2, T3, etc.).
        Estas temporales almacenan los resultados intermedios de las operaciones
        aritméticas antes de que el resultado final se asigne a una variable del usuario.
        
    Uso:
        Esta clase es utilizada exclusivamente por la función 'generar_cuadruplos'.
        Asegura que cada resultado intermedio tenga un nombre único para referenciarlo
        en las instrucciones de código intermedio.
    """
    def __init__(self):
        self.contador = 0
    
    def nuevo_temporal(self):
        self.contador += 1
        return f"T{self.contador}"

# Instancia global para el generador de temporales
# Se inicializa aquí para que la generación de nombres temporales sea secuencial
# a lo largo de todas las expresiones en el código fuente.
temp_generator = GeneradorTemporales()


# Conversión de Expresiones Infijas a Posfijas (RPN)
def infija_a_posfija(tokens_expresion):
    """
    Implementa el Algoritmo Shunting-yard de Dijkstra.
    
    Propósito:
        Convertir la expresión matemática escrita por el usuario (Notación Infija: a + b)
        a una Notación Polaca Inversa o Posfija (RPN: a b +).
        La RPN elimina la necesidad de paréntesis y la ambigüedad de la precedencia,
        haciendo que la evaluación o la generación de cuádruplos sea un proceso lineal.
        
    Estructuras de Datos:
        *pila_operadores*: **¡Usa una PILA!** Se utiliza para almacenar temporalmente
          los operadores y paréntesis, respetando su jerarquía antes de enviarlos a la salida.
        *salida_posfija*: **¡Usa una LISTA (como una Cola/Queue)!** Almacena la salida en
          el orden RPN. Se usa una lista simple de Python para ir agregando los tokens.
    """
    pila_operadores = []
    salida_posfija = []

    for token in tokens_expresion:
        if token not in PREDECENCIA and token not in [')', '(', '"', "'"]: 
            salida_posfija.append(token)
        elif token == '(':
            pila_operadores.append(token)
        elif token in PREDECENCIA:
            while (pila_operadores and pila_operadores[-1] != '(' and 
                   PREDECENCIA.get(pila_operadores[-1], 0) >= PREDECENCIA[token]):
                salida_posfija.append(pila_operadores.pop())
            pila_operadores.append(token)
        elif token == ')':
            while pila_operadores and pila_operadores[-1] != '(':
                salida_posfija.append(pila_operadores.pop())
            if pila_operadores and pila_operadores[-1] == '(':
                pila_operadores.pop()
    
    while pila_operadores:
        salida_posfija.append(pila_operadores.pop())
        
    return salida_posfija
# Generación de código intermedio (Cuádruplos)
def generar_cuadruplos(expresion_posfija, variables, generador_temporales):
    """
    Genera la secuencia de cuádruplos a partir de una expresión RPN.
    
    Propósito:
        Traducir la expresión RPN a una serie de instrucciones atómicas (cuádruplos).
        Cada cuádruplo tiene el formato: (Operador, Op1, Op2, Resultado).
        Esta fase prepara el código para la optimización y la generación de código máquina.
        
    Estructuras de Datos:
        pila_operandos: ¡Usa una PILA! Almacena los nombres de los operandos
        (IDs de variables o nombres de temporales como T1, T2) que serán usados
        por el siguiente operador.
    """
    pila_operandos = []
    lista_cuadruplos = []
    
    # Reiniciar el generador para cada expresión
    generador_temporales.contador = 0 
    
    try:
        for token in expresion_posfija:
            if token not in PREDECENCIA:  # Es un operando (ID, Constante, o Temporal de una expresión previa)
                pila_operandos.append(token)
            else:  # Es un operador
                if len(pila_operandos) < 2:
                     raise IndexError("Faltan operandos en la pila.")

                op2 = pila_operandos.pop()
                op1 = pila_operandos.pop()
                
                # Generar el nuevo temporal para almacenar el resultado
                resultado = generador_temporales.nuevo_temporal()
                
                # Crear el cuádruplo: (Operador, Op1, Op2, Resultado)
                cuadruplo = (token, op1, op2, resultado)
                lista_cuadruplos.append(cuadruplo)
                
                # Apilar el temporal para su uso posterior
                pila_operandos.append(resultado)

        resultado_final = pila_operandos[0] if pila_operandos else None
        
        return lista_cuadruplos, resultado_final
        
    except IndexError as e:
        return [], f"Error de sintaxis RPN: {e}"
    except Exception as e:
        return [], f"Error en generación de cuádruplos: {e}"

# Evaluación de Expresiones Posfijas (RPN)
def evaluar_posfija(expresion_posfija, variables):
    """
    Evalúa una expresión RPN para obtener un valor numérico.
    
    Propósito:
        Esta función solo se usa en este simulador para asignar un VALOR concreto
        a las variables en la Tabla de Variables, imitando la ejecución real
        del código. NO forma parte de la generación estándar de cuádruplos, pero
        complementa la fase semántica de este compilador de juguete.
        
    Estructuras de Datos:
        pila_operandos: ¡Usa una PILA! Almacena los valores numéricos
        (enteros o flotantes) que son el resultado de las operaciones.
    """
    pila_operandos = []
    
    try:
        for token in expresion_posfija:
            if token not in PREDECENCIA:
                if token.isdigit() or re.match(r'^-?\d+(\.\d+)?$', token):
                    valor = float(token) if '.' in token else int(token)
                elif token in variables:
                    valor_str = variables[token]['valor']
                    if valor_str is None or not re.match(r'^-?\d+(\.\d+)?$', str(valor_str)):
                         return f"Error: Valor no numérico para '{token}'"
                    valor = float(valor_str) if '.' in str(valor_str) else int(valor_str)
                else:
                    return f"Error: Variable '{token}' no declarada"
                
                pila_operandos.append(valor)
                
            else:
                op2 = pila_operandos.pop()
                op1 = pila_operandos.pop()
                
                if token == '+': resultado = op1 + op2
                elif token == '-': resultado = op1 - op2
                elif token == '*': resultado = op1 * op2
                elif token == '/': 
                    if op2 == 0: return "Error: División por cero"
                    resultado = op1 / op2
                    
                pila_operandos.append(resultado)

        return pila_operandos[0] if pila_operandos else None
        
    except (IndexError, NameError, ValueError, ZeroDivisionError) as e:
        return f"Error de evaluación: {e}"


# Fase Léxica y Semantica
def analizar_codigo_en_memoria(codigo):
    """
    FUNCIÓN PRINCIPAL DEL COMPILADOR (Analizador Léxico y Semántico).
    
    Propósito:
        1.  Análisis Léxico: Separar el código fuente en tokens (lexemas).
        2.  Análisis Semántico (Variables): Administrar la Tabla de Variables,
            verificar declaración, tipo y uso de identificadores.
        3.  Generación de Cuádruplos: Para líneas de asignación de expresiones.
    """    
    global current_cuadruplos # Variable global para almacenar todos los cuádruplos generados
    
    tokens = []
    variables = {}
    errores = []
    lexemas_depurados = []
    current_cuadruplos = [] # Limpiar la lista de cuádruplos al inicio
    
    lineas = codigo.splitlines()
    
    for num_linea, linea in enumerate(lineas, 1):
        if not linea.strip(): continue
        if linea.startswith('--'): continue
            
        elementos = []
        partes = linea.split('--', 1) 
        codigo_sin_comentario = partes[0].strip()
        
        if codigo_sin_comentario:
            elementos = re.findall(r'\"[^\"]*\"|\'[^\']*\'|[+\-*/=()]|\S+', codigo_sin_comentario)
            lexemas_depurados.extend(elementos)
        
        i = 0
        while i < len(elementos):
            lexema = elementos[i]
            
            # DECLARACIÓN DE VARIABLE (Lógica para Cuádruplos)
            if lexema in ['Entero', 'Cadena', 'Boleano', 'Numero'] and i + 1 < len(elementos):
                tipo_var = lexema
                nombre_var = elementos[i + 1]
                
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', nombre_var):
                    if nombre_var in variables:
                        errores.append(f"Linea: {num_linea} Error: Variable '{nombre_var}' ya declarada")
                    else:
                        variables[nombre_var] = {'linea': num_linea, 'tipo': tipo_var, 'valor': None, 'asignada': False}
                    
                    if i + 2 < len(elementos) and elementos[i + 2] == '=':
                        inicio_expresion_idx = i + 3
                        expresion_tokens = elementos[inicio_expresion_idx:]
                        
                        if tipo_var in ['Entero', 'Numero'] and expresion_tokens:
                            try:
                                # 1. Generar Posfija
                                expresion_posfija = infija_a_posfija(expresion_tokens)
                                
                                # 2. GENERAR CUÁDRUPLOS
                                lista_cuadruplos_gen, temporal_final = generar_cuadruplos(expresion_posfija, variables, temp_generator)
                                
                                # Anexar los cuádruplos de la expresión
                                current_cuadruplos.extend(lista_cuadruplos_gen)
                                
                                # Generar Cuádruplo de Asignación Final
                                if temporal_final:
                                    # La asignación final es el cuádruplo: ('=', temporal_final, '_', variable_destino)
                                    cuadruplo_asignacion = ('=', temporal_final, '_', nombre_var)
                                    current_cuadruplos.append(cuadruplo_asignacion)
                                
                                # 3. EVALUAR (Para la Tabla de Variables)
                                resultado_evaluacion = evaluar_posfija(expresion_posfija, variables)
                                
                                if isinstance(resultado_evaluacion, str) and resultado_evaluacion.startswith("Error"):
                                    errores.append(f"Linea: {num_linea} Error de Expresión: {resultado_evaluacion}")
                                else:
                                    # Asignar el resultado numérico
                                    variables[nombre_var]['valor'] = int(resultado_evaluacion) if tipo_var == 'Entero' else resultado_evaluacion
                                    variables[nombre_var]['asignada'] = True
                                    
                            except Exception as e:
                                errores.append(f"Linea: {num_linea} Error en la conversión/generación de cuádruplos: {e}")
                        
                        # Manejo de asignación simple (Cadenas, Booleanos, o solo constantes/ID sin operación)
                        elif len(expresion_tokens) == 1:
                            # Lógica original de tu compilador para tipos no aritméticos
                            valor_asignado = expresion_tokens[0]
                            if tipo_var == 'Cadena':
                                if not ((valor_asignado.startswith('"') and valor_asignado.endswith('"')) or (valor_asignado.startswith("'") and valor_asignado.endswith("'"))):
                                    errores.append(f"Linea: {num_linea} Error: Se esperaba Cadena para '{nombre_var}'")
                                else:
                                    variables[nombre_var]['valor'] = valor_asignado
                                    variables[nombre_var]['asignada'] = True
                                    # Generar Cuádruplo de Asignación Simple
                                    current_cuadruplos.append(('=', valor_asignado, '_', nombre_var))

                        # Lógica para saltar la línea ya procesada
                        i += len(elementos) - i
                        continue
                    
                    i += 2
                    continue
            
            # --- Generación de Tokens (Resto de la lógica original) ---
            token_type = None
            ref = 99
            
            # (El resto de la lógica de tokenización se mantiene igual)
            if (lexema.startswith('"') and lexema.endswith('"')) or (lexema.startswith("'") and lexema.endswith("'")):
                token_type = 'CADENA'
                ref = 4
            elif lexema in ['Entero', 'Cadena', 'Boleano', 'Inicio', 'Fin', 'Tigre', 'Numero']:
                token_type = 'PALABRA_RESERVADA'
                ref = 1
            elif lexema.lower() in ['true', 'false']: 
                token_type = 'CONSTANTE_BOOLEANA'
                ref = 4
            elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', lexema):
                token_type = 'IDENTIFICADOR'
                ref = 2
                if (i == 0 or elementos[i-1] not in ['Entero', 'Cadena', 'Boleano', 'Numero', '=', '(', '+', '-', '*', '/']):
                    if lexema not in variables:
                        errores.append(f"Linea: {num_linea} Error: Variable '{lexema}' no declarada")
            elif lexema == '=':
                token_type = 'ASIGNACION'
                ref = 3
            elif lexema in ['+', '-', '*', '/']:
                token_type = 'OPERADOR'
                ref = 5
            elif lexema in ['(', ')']:
                token_type = 'DELIMITADOR'
                ref = 6
            elif re.match(r'^-?\d+(\.\d+)?$', lexema): 
                token_type = 'CONSTANTE_NUMERICA'
                ref = 4
            else:
                token_type = 'ERROR'
                ref = 99
                errores.append(f"Linea: {num_linea} Error: Lexema '{lexema}' no reconocido")
            
            tokens.append({
                'Linea': num_linea,
                'Lexema': lexema,
                'Token': token_type,
                'Referencia': ref
            })
            
            i += 1
    
    return tokens, variables, errores, lexemas_depurados

# --- FUNCIONES AUXILIARES Y GUI (Adaptadas) ---

def generar_tabla_cuadruplos_str(cuadruplos):
    """Genera la tabla de cuádruplos como una cadena de texto."""
    output = f"{'No.':<5} {'Operador':<15} {'Op1':<10} {'Op2':<10} {'Resultado':<10}\n"
    output += "-" * 65 + "\n"
    if not cuadruplos:
        return output + "No se generaron cuádruplos para expresiones."
        
    for i, (op, arg1, arg2, result) in enumerate(cuadruplos):
        output += f"{i:<5} {op:<15} {str(arg1):<10} {str(arg2):<10} {str(result):<10}\n"
    return output

# Variables globales para almacenar los resultados del análisis
current_tokens = []
current_variables = {}
current_errors = []
current_lexemas_depurados = []
current_cuadruplos = [] # NUEVA VARIABLE GLOBAL

# (Resto de las funciones auxiliares se mantienen igual: generar_archivo, generar_tabla_str)
def generar_archivo_depurado(lexemas_depurados, nombre_archivo):
    with open(nombre_archivo, 'w', encoding='utf-8') as archivo:
        contenido = ''.join(lexemas_depurados) 
        archivo.write(contenido)

def generar_archivo_tokens(tokens, nombre_archivo):
    with open(nombre_archivo, 'w', encoding='utf-8') as archivo:
        archivo.write(f"{'Linea:':<12} {'Lexema:':<20} {'Token:'}\n")
        archivo.write("-" * 65 + "\n")
        for token in tokens:
            archivo.write(f"{token['Linea']:<12} {token['Lexema']:<20} {token['Token']}\n")

def generar_tabla_simbolos(tokens, nombre_archivo_salida):
    with open(nombre_archivo_salida, 'w', encoding='utf-8') as archivo:
        archivo.write(f"{'No.':<5} {'Lexema':<20} {'Token':<20} {'Referencia':<10}\n")
        archivo.write("-" * 65 + "\n")
        for i, token in enumerate(tokens):
            archivo.write(f"{i:<5} {token['Lexema']:<20} {token['Token']:<20} {token['Referencia']:<10}\n")

def generar_tabla_variables(variables, nombre_archivo_salida):
    with open(nombre_archivo_salida, 'w', encoding='utf-8') as archivo:
        archivo.write(f"{'Variable':<15} {'Linea':<8} {'Tipo':<12} {'Asignada':<10} {'Valor':<20}\n")
        archivo.write("-" * 65 + "\n")
        for var_name, info in variables.items():
            valor_str = str(info['valor']) if info['valor'] is not None else 'None'
            archivo.write(f"{var_name:<15} {info['linea']:<8} {info['tipo']:<12} {str(info['asignada']):<10} {valor_str:<20}\n")

def generar_tabla_simbolos_str(tokens):
    output = f"{'No.':<5} {'Lexema':<20} {'Token':<20} {'Referencia':<10}\n"
    output += "-" * 65 + "\n"
    for i, token in enumerate(tokens):
        output += f"{i:<5} {token['Lexema']:<20} {token['Token']:<20} {token['Referencia']:<10}\n"
    return output

def generar_tabla_variables_str(variables):
    output = f"{'Variable':<15} {'Linea':<8} {'Tipo':<12} {'Asignada':<10} {'Valor':<20}\n"
    output += "-" * 65 + "\n"
    for var_name, info in variables.items():
        valor_str = str(info['valor']) if info['valor'] is not None else 'None'
        output += f"{var_name:<15} {info['linea']:<8} {info['tipo']:<12} {str(info['asignada']):<10} {valor_str:<20}\n"
    return output

def generar_tabla_tokens_str(tokens):
    output = f"{'Linea:':<12} {'Lexema:':<20} {'Token:'}\n"
    output += "-" * 65 + "\n"
    for token in tokens:
        output += f"{token['Linea']:<12} {token['Lexema']:<20} {token['Token']}\n"
    return output

def generar_codigo_depurado_str(lexemas_depurados):
    return ''.join(lexemas_depurados)


def run_code():
    global current_tokens, current_variables, current_errors, current_lexemas_depurados, current_cuadruplos
    
    code_to_compile = editor_area.get("1.0", tk.END).strip()
    
    console_area.config(state=tk.NORMAL)
    console_area.delete("1.0", tk.END)
    
    if not code_to_compile:
        console_area.insert(tk.END, ">>> Editor vacío. No hay código para analizar.\n", "error_tag")
        console_area.config(state=tk.DISABLED)
        return

    try:
        current_tokens, current_variables, current_errors, current_lexemas_depurados = analizar_codigo_en_memoria(code_to_compile)

        # Generar archivos
        generar_tabla_simbolos(current_tokens, 'progfte.tab')
        generar_tabla_variables(current_variables, 'variables.tab')
        generar_archivo_depurado(current_lexemas_depurados, 'progfte.dep')
        generar_archivo_tokens(current_tokens, 'progfte.tok')
        
        console_area.insert(tk.END, ">>> Análisis completado. Archivos generados.\n", "output_tag")

        if current_errors:
            console_area.insert(tk.END, "[Errores de Sintaxis/Semántica]:\n", "error_tag")
            for error in current_errors:
                console_area.insert(tk.END, f"  - {error}\n", "error_tag")
        else:
            console_area.insert(tk.END, ">>> No se encontraron errores.\n", "output_tag")
            console_area.insert(tk.END, f"\nCuádruplos generados: {len(current_cuadruplos)}\n", "output_tag")

    except Exception as e:
        console_area.insert(tk.END, f">>> Ocurrió un error inesperado: {e}\n", "error_tag")

    console_area.config(state=tk.DISABLED)

def show_tables_view():
    global current_tokens, current_variables, current_lexemas_depurados, current_cuadruplos
    
    tables_area.config(state=tk.NORMAL)
    tables_area.delete("1.0", tk.END)
    
    if not current_tokens:
        tables_area.insert(tk.END, ">>> No hay tokens para mostrar. Ejecute el código primero.\n", "error_tag")
    else:
        # TÍTULOS Y CONTENIDO
        tables_area.insert(tk.END, "TABLA DE CUÁDRUPLOS (Código Intermedio):\n")
        tables_area.insert(tk.END, generar_tabla_cuadruplos_str(current_cuadruplos))
        
        tables_area.insert(tk.END, "-" * 60 + "\n")

        tables_area.insert(tk.END, "\n\nTABLA DE SÍMBOLOS:\n")
        tables_area.insert(tk.END, generar_tabla_simbolos_str(current_tokens))
        
        tables_area.insert(tk.END, "\n\nTABLA DE VARIABLES (Valores Evaluados):\n")
        tables_area.insert(tk.END, generar_tabla_variables_str(current_variables))
        
        tables_area.insert(tk.END, "\n\nCÓDIGO DEPURADO:\n")
        tables_area.insert(tk.END, generar_codigo_depurado_str(current_lexemas_depurados))

    tables_area.config(state=tk.DISABLED)

    editor_frame.pack_forget()
    console_frame.pack_forget()
    tables_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    show_tables_button.config(state=tk.DISABLED)
    run_button.config(state=tk.DISABLED)
    back_button.config(state=tk.NORMAL)
    
def show_editor_view():
    tables_frame.pack_forget()
    editor_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
    console_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

    show_tables_button.config(state=tk.NORMAL)
    run_button.config(state=tk.NORMAL)
    back_button.config(state=tk.DISABLED)

# --- Configuración de la ventana principal ---
root = tk.Tk()
root.title("Compilador TigerPy")
root.geometry("850x650")

# Variables globales para almacenar los resultados del análisis
current_tokens = []
current_variables = {}
current_errors = []
current_lexemas_depurados = []
current_cuadruplos = []

# --- Frames ---
button_frame = tk.Frame(root, padx=5, pady=5)
button_frame.pack(side=tk.TOP, fill=tk.X)
editor_frame = tk.Frame(root)
console_frame = tk.Frame(root)
tables_frame = tk.Frame(root)

# --- Elementos de la GUI ---
run_button = tk.Button(button_frame, text="Ejecutar", font=("Arial", 12), command=run_code)
run_button.pack(side=tk.LEFT, padx=(0, 5))

show_tables_button = tk.Button(button_frame, text="Información/Cuádruplos", font=("Arial", 12), command=show_tables_view)
show_tables_button.pack(side=tk.LEFT, padx=(0, 5))

back_button = tk.Button(button_frame, text="Volver", font=("Arial", 12), command=show_editor_view)
back_button.pack(side=tk.LEFT)
back_button.config(state=tk.DISABLED) 

# Área de texto del editor
editor_area = scrolledtext.ScrolledText(
    editor_frame, wrap=tk.WORD, padx=10, pady=10, font=("Courier New", 12), bg="#1e1e1e", fg="#dcdcdc", insertbackground="white"
)
editor_area.pack(fill=tk.BOTH, expand=True)

# Contenido inicial
initial_text = """-- Ejemplo de código TigerPy (Código de prueba)
Inicio
        Entero a = 10
        Entero b = 5
        
        -- Expresión aritmética
        Entero resultado = a + b * ( 20 - a ) / 2
        
        -- Asignación
        Cadena nombre = "TigerPy"
        
        -- Expresión con error
        Entero error_div = 10 / 0 
        
Fin"""

editor_area.insert(tk.END, initial_text)

# Área de texto de la consola
console_area = scrolledtext.ScrolledText(
    console_frame, wrap=tk.WORD, padx=10, pady=10, height=10, font=("Courier New", 12), bg="#1e1e1e", fg="#70dc70", state=tk.DISABLED
)
console_area.pack(fill=tk.BOTH, expand=True)

# Área de texto para mostrar las tablas
tables_area = scrolledtext.ScrolledText(
    tables_frame, wrap=tk.WORD, padx=10, pady=10, font=("Courier New", 12), bg="#1e1e1e", fg="#dcdcdc", state=tk.DISABLED
)
tables_area.pack(fill=tk.BOTH, expand=True)

# Tags para colorear la salida y los errores en la consola
console_area.tag_configure("output_tag", foreground="#ffffff")
console_area.tag_configure("error_tag", foreground="#ff6347")
console_area.tag_configure("prompt_tag", foreground="#00ff00")

# Iniciar con la vista del editor
editor_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
console_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

# --- Bucle principal ---
root.mainloop()