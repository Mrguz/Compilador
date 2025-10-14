import tkinter as tk
from tkinter import scrolledtext
import re
import os

# Diccionario de Precedencia (Jerarquía de Operadores)
PREDECENCIA = {
    '+': 1, '-': 1,
    '*': 2, '/': 2,
    '(': 0 
}

class GeneradorTemporales:
    def __init__(self):
        self.contador = 0
    
    def nuevo_temporal(self):
        self.contador += 1
        return f"T{self.contador}"

temp_generator = GeneradorTemporales()


# --- FUNCIONES DE ANÁLISIS Y OPTIMIZACIÓN ---

def infija_a_posfija(tokens_expresion):
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

def generar_cuadruplos(expresion_posfija, variables, generador_temporales):
    pila_operandos = []
    lista_cuadruplos = []
    generador_temporales.contador = 0 
    try:
        for token in expresion_posfija:
            if token not in PREDECENCIA:
                pila_operandos.append(token)
            else:
                if len(pila_operandos) < 2: raise IndexError("Faltan operandos en la pila.")
                op2 = pila_operandos.pop()
                op1 = pila_operandos.pop()
                resultado = generador_temporales.nuevo_temporal()
                cuadruplo = (token, op1, op2, resultado)
                lista_cuadruplos.append(cuadruplo)
                pila_operandos.append(resultado)
        resultado_final = pila_operandos[0] if pila_operandos else None
        return lista_cuadruplos, resultado_final
    except Exception as e:
        return [], f"Error en generación de cuádruplos: {e}"

def evaluar_posfija(expresion_posfija, variables):
    pila_operandos = []
    try:
        for token in expresion_posfija:
            if token not in PREDECENCIA:
                if token.isdigit() or re.match(r'^-?\d+(\.\d+)?$', token):
                    valor = float(token) if '.' in token else int(token)
                elif token in variables:
                    valor_str = variables[token]['valor']
                    if valor_str is None or not re.match(r'^-?\d+(\.\d+)?$', str(valor_str)):
                        if str(valor_str).lower() == 'true': valor = 1
                        elif str(valor_str).lower() == 'false': valor = 0
                        else: return f"Error: Valor no numérico para '{token}'"
                    else:
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
    except Exception as e:
        return f"Error de evaluación: {e}"

def es_constante_numerica(token):
    return re.match(r'^-?\d+(\.\d+)?$', str(token)) or str(token).lower() in ['true', 'false', '1', '0']

def obtener_valor_numerico(token):
    token_str = str(token)
    if token_str.lower() == 'true' or token_str == '1': return 1
    if token_str.lower() == 'false' or token_str == '0': return 0
    if es_constante_numerica(token_str):
        if token_str.isdigit() or re.match(r'^-?\d+$', token_str): return int(token_str)
        if re.match(r'^-?\d+(\.\d+)?$', token_str): return float(token_str)
    return None

def optimizar_cuadruplos(lista_cuadruplos, variables):
    if not lista_cuadruplos: return []
    expresiones_vistas = {}
    valor_map = {}
    for nombre_var, info in variables.items():
        val = info['valor']
        if val is not None:
            if info['tipo'] == 'Boleano':
                valor_map[nombre_var] = 1 if val is True else 0
            elif es_constante_numerica(val):
                valor_map[nombre_var] = obtener_valor_numerico(val)

    cuadruplos_intermedios = []
    for op, arg1, arg2, result in lista_cuadruplos:
        while arg1 in valor_map and not str(valor_map[arg1]).startswith(('"', "'")): arg1 = valor_map[arg1]
        while arg2 in valor_map and not str(valor_map[arg2]).startswith(('"', "'")): arg2 = valor_map[arg2]

        val_arg1 = obtener_valor_numerico(arg1)
        val_arg2 = obtener_valor_numerico(arg2)
        
        if op == '=':
            if str(arg1).startswith(('"', "'")):
                cuadruplos_intermedios.append((op, arg1, arg2, result))
                continue
            if val_arg1 is not None:
                valor_map[result] = val_arg1
            else: 
                valor_map[result] = arg1
            cuadruplos_intermedios.append((op, arg1, arg2, result))
            continue
        
        if val_arg1 is not None and val_arg2 is not None and op in ['+', '-', '*', '/']:
            try:
                if op == '+': new_value = val_arg1 + val_arg2
                elif op == '-': new_value = val_arg1 - val_arg2
                elif op == '*': new_value = val_arg1 * val_arg2
                elif op == '/' and val_arg2 != 0: new_value = val_arg1 / val_arg2
                else: new_value = None
                
                if new_value is not None:
                    if new_value == int(new_value): new_value = int(new_value)
                    cuadruplos_intermedios.append(('=', new_value, '_', result))
                    valor_map[result] = new_value
                    continue
            except: pass 

        key = (op, min(str(arg1), str(arg2)), max(str(arg1), str(arg2))) if op in ['+', '*'] else (op, str(arg1), str(arg2))
        if key in expresiones_vistas:
            temp_anterior = expresiones_vistas[key]
            cuadruplos_intermedios.append(('=', temp_anterior, '_', result))
            valor_map[result] = temp_anterior
        else:
            expresiones_vistas[key] = result
            cuadruplos_intermedios.append((op, arg1, arg2, result))

    usados = set(variables.keys())
    for op, arg1, arg2, result in reversed(cuadruplos_intermedios):
        if result in usados:
            if not es_constante_numerica(arg1) and not str(arg1).startswith(('"', "'")): usados.add(arg1)
            if arg2 != '_' and not es_constante_numerica(arg2) and not str(arg2).startswith(('"', "'")): usados.add(arg2)

    cuadruplos_finales = []
    for quad in cuadruplos_intermedios:
        _, _, _, result = quad
        if result in usados:
            if not (quad[0] == '=' and quad[1] == quad[3]):
                cuadruplos_finales.append(quad)
    return cuadruplos_finales


# --- FASE DE GENERACIÓN DE CÓDIGO ENSAMBLADOR ---

current_masm_code = ""

def generar_codigo_ensamblador_masm(cuadruplos_optimizados, variables):
    global current_masm_code
    identificadores = set()
    for _, op1, op2, result in cuadruplos_optimizados:
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(op1)) and not es_constante_numerica(op1) and not str(op1).startswith(('"', "'")): identificadores.add(str(op1))
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(op2)) and not es_constante_numerica(op2) and op2 != '_' and not str(op2).startswith(('"', "'")): identificadores.add(str(op2))
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(result)) and not es_constante_numerica(result) and not str(result).startswith(('"', "'")): identificadores.add(str(result))

    data_section = "\n.DATA\n"
    for var_name, info in variables.items():
        if var_name in identificadores:
            var_type = info['tipo']
            initial_value = info['valor']
            if var_type in ['Entero', 'Numero', 'Boleano']:
                data_section += f"    {var_name:<8} DW  0\n"
            elif var_type == 'Cadena':
                if initial_value is not None and not str(initial_value).startswith(('"', "'")):
                    data_section += f"    {var_name:<8} DB  '{initial_value}', '$'\n"
                else:
                    data_section += f"    {var_name:<8} DB  255 DUP('$') ; Reservar 255 bytes\n"
            identificadores.discard(var_name)
    
    for temp in sorted([i for i in identificadores if i.startswith('T')]):
        data_section += f"    {temp:<8} DW  0\n"

    code_body = ""
    for op, arg1, arg2, result in cuadruplos_optimizados:
        arg1_src = str(arg1)
        arg2_src = str(arg2)
        is_string_assignment = variables.get(result, {}).get('tipo') == 'Cadena'

        
        if op == '=':
            if is_string_assignment:
                code_body += f"    ; Asignación de Cadena omitida (inicializada en .DATA)\n"
                continue
            
            if es_constante_numerica(arg1_src):
                val = obtener_valor_numerico(arg1_src)
                if val is not None:
                    code_body += f"    MOV {result}, {val}\n"
                else:
                    code_body += f"    MOV AX, {arg1_src}\n"
                    code_body += f"    MOV {result}, AX\n"
            else:
                code_body += f"    MOV AX, {arg1_src}\n"
                code_body += f"    MOV {result}, AX\n"
        
        elif op in ['+', '-', '*', '/']:
            val1 = obtener_valor_numerico(arg1_src)
            val2 = obtener_valor_numerico(arg2_src)

            if val1 is not None: code_body += f"    MOV AX, {val1}\n"
            else: code_body += f"    MOV AX, {arg1_src}\n"

            if val2 is not None: code_body += f"    MOV BX, {val2}\n"
            else: code_body += f"    MOV BX, {arg2_src}\n"
            
            if op == '+': code_body += f"    ADD AX, BX\n"
            elif op == '-': code_body += f"    SUB AX, BX\n"
            elif op == '*': code_body += f"    IMUL BX\n" 
            elif op == '/': 
                code_body += f"    MOV DX, 0\n" 
                code_body += f"    IDIV BX\n"
            
            code_body += f"    MOV {result}, AX\n"

    masm_template = f"""
.MODEL SMALL
.STACK 100H

{data_section}

.CODE
MAIN PROC
    ; Inicializar segmento de datos
    MOV AX, @DATA
    MOV DS, AX

    ; Código generado a partir de cuádruplos:
{code_body}

    ; Salir al DOS
    MOV AH, 4CH
    INT 21H
MAIN ENDP
END MAIN
"""
    current_masm_code = masm_template.strip()
    return current_masm_code


# --- FASE LÉXICA Y SEMANTICA ---

def analizar_codigo_en_memoria(codigo):
    tokens = []
    variables = {}
    errores = []
    lexemas_depurados = []
    lista_cuadruplos_resultante = [] 
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
                        
                        if (tipo_var in ['Entero', 'Numero']) and any(op in expresion_tokens for op in PREDECENCIA.keys()):
                            try:
                                expresion_posfija = infija_a_posfija(expresion_tokens)
                                lista_cuadruplos_gen, temporal_final = generar_cuadruplos(expresion_posfija, variables, temp_generator)
                                lista_cuadruplos_resultante.extend(lista_cuadruplos_gen)
                                
                                if temporal_final:
                                    lista_cuadruplos_resultante.append(('=', temporal_final, '_', nombre_var))
                                
                                resultado_evaluacion = evaluar_posfija(expresion_posfija, variables)
                                
                                if isinstance(resultado_evaluacion, str) and resultado_evaluacion.startswith("Error"):
                                    errores.append(f"Linea: {num_linea} Error de Expresión: {resultado_evaluacion}")
                                else:
                                    if tipo_var == 'Entero': variables[nombre_var]['valor'] = int(resultado_evaluacion)
                                    elif tipo_var == 'Boleano': variables[nombre_var]['valor'] = True if resultado_evaluacion == 1 else False
                                    else: variables[nombre_var]['valor'] = resultado_evaluacion
                                    variables[nombre_var]['asignada'] = True
                                    
                            except Exception as e:
                                errores.append(f"Linea: {num_linea} Error en la conversión/generación de cuádruplos: {e}")
                            
                        elif len(expresion_tokens) == 1:
                            valor_asignado = expresion_tokens[0]
                            
                            if tipo_var == 'Cadena':
                                if not ((valor_asignado.startswith('"') and valor_asignado.endswith('"')) or (valor_asignado.startswith("'") and valor_asignado.endswith("'"))):
                                    errores.append(f"Linea: {num_linea} Error: Se esperaba Cadena para '{nombre_var}'")
                                else:
                                    variables[nombre_var]['valor'] = valor_asignado[1:-1]
                                    variables[nombre_var]['asignada'] = True
                                    lista_cuadruplos_resultante.append(('=', valor_asignado, '_', nombre_var))
                                    
                            elif tipo_var == 'Boleano': 
                                if valor_asignado.lower() == 'true':
                                    variables[nombre_var]['valor'] = True
                                    variables[nombre_var]['asignada'] = True
                                    lista_cuadruplos_resultante.append(('=', '1', '_', nombre_var)) 
                                elif valor_asignado.lower() == 'false':
                                    variables[nombre_var]['valor'] = False
                                    variables[nombre_var]['asignada'] = True
                                    lista_cuadruplos_resultante.append(('=', '0', '_', nombre_var))
                                else:
                                    if valor_asignado in variables and variables[valor_asignado]['tipo'] == 'Boleano':
                                        variables[nombre_var]['valor'] = variables[valor_asignado]['valor']
                                        variables[nombre_var]['asignada'] = True
                                        lista_cuadruplos_resultante.append(('=', valor_asignado, '_', nombre_var))
                                    else:
                                        errores.append(f"Linea: {num_linea} Error: Se esperaba True, False o una variable Boleana para '{nombre_var}'")
                                    
                            elif tipo_var in ['Entero', 'Numero'] and (es_constante_numerica(valor_asignado) or valor_asignado in variables):
                                lista_cuadruplos_resultante.append(('=', valor_asignado, '_', nombre_var))
                                
                                try:
                                    valor_num = obtener_valor_numerico(valor_asignado)
                                    if valor_num is None and valor_asignado in variables: valor_num = variables[valor_asignado]['valor']
                                        
                                    if valor_num is not None: variables[nombre_var]['valor'] = valor_num
                                    else: variables[nombre_var]['valor'] = valor_asignado
                                    variables[nombre_var]['asignada'] = True
                                        
                                except Exception as e:
                                    errores.append(f"Linea: {num_linea} Error de asignación simple: {e}")
                                    
                            else:
                                errores.append(f"Linea: {num_linea} Error: Tipo de asignación incompatible para '{nombre_var}'")

                        i += len(elementos) - i
                        continue
                    
                    i += 2
                    continue
                
            # --- GENERACIÓN DE TOKENS (LÉXICO) ---
            token_type = None
            ref = 99
            
            if lexema.lower() in ['true', 'false']: 
                token_type = 'CONSTANTE_BOOLEANA'
                ref = 4
            elif (lexema.startswith('"') and lexema.endswith('"')) or (lexema.startswith("'") and lexema.endswith("'")):
                token_type = 'CADENA'
                ref = 4
            elif lexema in ['Entero', 'Cadena', 'Boleano', 'Inicio', 'Fin', 'Numero']:
                token_type = 'PALABRA_RESERVADA'
                ref = 1
            elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', lexema):
                token_type = 'IDENTIFICADOR'
                ref = 2
                if (i == 0 or elementos[i-1] not in ['Entero', 'Cadena', 'Boleano', 'Numero', '=', '(', '+', '-', '*', '/']):
                    if lexema not in variables and lexema.lower() not in ['true', 'false']:
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
    
    return tokens, variables, errores, lexemas_depurados, lista_cuadruplos_resultante

# --- FUNCIONES DE GENERACIÓN DE TABLAS (STRINGS) ---

# Variables globales para almacenar los resultados del análisis
current_tokens = []
current_variables = {}
current_errors = []
current_lexemas_depurados = []
current_cuadruplos = []
optimized_cuadruplos = [] 
current_masm_code = ""

def generar_tabla_simbolos_str(tokens, variables):
    """Genera la tabla de símbolos con Lexema, Tipo de Dato y Categoría."""
    simbolos_map = {}
    
    for token in tokens:
        lexema = token['Lexema']
        
        if token['Token'] in ['OPERADOR', 'ASIGNACION', 'DELIMITADOR', 'CONSTANTE_NUMERICA', 'CADENA']:
            continue
            
        categoria = "Palabra Reservada"
        tipo_dato = "N/A"
        
        if lexema in variables:
            categoria = "Variable"
            tipo_dato = variables[lexema]['tipo']
        elif token['Token'] == 'IDENTIFICADOR':
            categoria = "Identificador (No asignado)"
        elif lexema in ['Entero', 'Numero', 'Cadena', 'Boleano']:
            tipo_dato = lexema
        elif lexema in ['True', 'False', 'true', 'false']:
            tipo_dato = "Boleano"
            categoria = "Constante"
        elif lexema in ['Inicio', 'Fin']:
            categoria = "Estructura"

        if lexema not in simbolos_map:
            simbolos_map[lexema] = {
                'Lexema': lexema,
                'Tipo': tipo_dato,
                'Categoria': categoria,
            }

    output = f"{'Nombre del Símbolo':<25} {'Tipo de Dato':<15} {'Categoría/Clase':<30}\n"
    output += "-" * 70 + "\n"
    
    for sim_info in simbolos_map.values():
        output += f"{sim_info['Lexema']:<25} {sim_info['Tipo']:<15} {sim_info['Categoria']:<30}\n"
        
    return output

def generar_tabla_tokens_str(tokens):
    """Genera la tabla de tokens con Línea, Lexema y Tipo de Token."""
    output = f"{'Línea':<8} {'Lexema (Secuencia de Caracteres)':<35} {'Tipo de Token'}\n"
    output += "-" * 70 + "\n"
    for token in tokens:
        output += f"{token['Linea']:<8} {token['Lexema']:<35} {token['Token']}\n"
    return output

def generar_tabla_variables_str(variables):
    """Genera la tabla de variables con sus valores finales."""
    output = f"{'Variable':<15} {'Tipo':<12} {'Asignada':<10} {'Valor (Final)':<25}\n"
    output += "-" * 65 + "\n"
    for var_name, info in variables.items():
        valor_str = str(info['valor']) if info['valor'] is not None else 'None'
        output += f"{var_name:<15} {info['tipo']:<12} {str(info['asignada']):<10} {valor_str:<25}\n"
    return output

def generar_tabla_cuadruplos_str(cuadruplos):
    """Genera la tabla de cuádruplos como una cadena de texto."""
    output = f"{'No.':<5} {'Operador':<15} {'Op1':<10} {'Op2':<10} {'Resultado':<10}\n"
    output += "-" * 65 + "\n"
    if not cuadruplos:
        return output + "No se generaron cuádruplos para expresiones."
        
    for i, (op, arg1, arg2, result) in enumerate(cuadruplos):
        output += f"{i:<5} {op:<15} {str(arg1):<10} {str(arg2):<10} {str(result):<10}\n"
    return output

def generar_codigo_depurado_str(lexemas_depurados):
    return ''.join(lexemas_depurados)


# --- FUNCIONES DE CONTROL DE LA GUI ---

def run_code():
    global current_tokens, current_variables, current_errors, current_lexemas_depurados, current_cuadruplos, optimized_cuadruplos, current_masm_code
    
    code_to_compile = editor_area.get("1.0", tk.END).strip()
    
    console_area.config(state=tk.NORMAL)
    console_area.delete("1.0", tk.END)
    
    if not code_to_compile:
        console_area.insert(tk.END, ">>> Editor vacío. No hay código para analizar.\n", "error_tag")
        console_area.config(state=tk.DISABLED)
        return

    try:
        current_tokens, current_variables, current_errors, current_lexemas_depurados, current_cuadruplos = analizar_codigo_en_memoria(code_to_compile)

        optimized_cuadruplos = optimizar_cuadruplos(current_cuadruplos, current_variables)
        
        if not current_errors:
            codigo_masm = generar_codigo_ensamblador_masm(optimized_cuadruplos, current_variables)
            with open('progfte.asm', 'w', encoding='utf-8') as f: f.write(codigo_masm)
        else:
            current_masm_code = "No se pudo generar el código ensamblador debido a errores o falta de cuádruplos."
        
        console_area.insert(tk.END, ">>> Análisis y Optimización completados. Archivos generados.\n", "output_tag")

        if current_errors:
            console_area.insert(tk.END, "[Errores de Sintaxis/Semántica]:\n", "error_tag")
            for error in current_errors:
                console_area.insert(tk.END, f"  - {error}\n", "error_tag")
        else:
            console_area.insert(tk.END, ">>> No se encontraron errores.\n", "output_tag")
            console_area.insert(tk.END, f"\nCuádruplos Originales: {len(current_cuadruplos)}\n", "output_tag")
            console_area.insert(tk.END, f"Cuádruplos Optimizados: {len(optimized_cuadruplos)}\n", "output_tag")

    except Exception as e:
        console_area.insert(tk.END, f">>> Ocurrió un error inesperado: {e}\n", "error_tag")

    console_area.config(state=tk.DISABLED)

def show_tables_view():
    global current_tokens, current_variables, current_lexemas_depurados, current_cuadruplos, optimized_cuadruplos, current_masm_code
    
    tables_area.config(state=tk.NORMAL)
    tables_area.delete("1.0", tk.END)
    
    if not current_tokens:
        tables_area.insert(tk.END, ">>> No hay tokens para mostrar. Ejecute el código primero.\n", "error_tag")
    else:
        # Tablas Semánticas y Léxicas
        tables_area.insert(tk.END, "TABLA DE SÍMBOLOS (SEMÁNTICA)\n")
        tables_area.insert(tk.END, generar_tabla_simbolos_str(current_tokens, current_variables))
        
        tables_area.insert(tk.END, "\n" + "_" * 70 + "\n")

        tables_area.insert(tk.END, "\nTABLA DE TOKENS (LÉXICA)\n")
        tables_area.insert(tk.END, generar_tabla_tokens_str(current_tokens))
        
        tables_area.insert(tk.END, "\n" + "_" * 70 + "\n")
        
        tables_area.insert(tk.END, "\nTABLA DE VARIABLES (Valores Finales)\n")
        tables_area.insert(tk.END, generar_tabla_variables_str(current_variables))
        
        tables_area.insert(tk.END, "\n" + "_" * 70 + "\n")
        
        # Cuádruplos y Ensamblador
        tables_area.insert(tk.END, "\nTABLA DE CUÁDRUPLOS (ORIGINAL):\n")
        tables_area.insert(tk.END, generar_tabla_cuadruplos_str(current_cuadruplos))
        
        tables_area.insert(tk.END, "\n" + "_" * 70 + "\n")
        
        tables_area.insert(tk.END, "\nTABLA DE CUÁDRUPLOS (OPTIMIZADO):\n")
        tables_area.insert(tk.END, generar_tabla_cuadruplos_str(optimized_cuadruplos))
        
        tables_area.insert(tk.END, "\n" + "_" * 70 + "\n")

        tables_area.insert(tk.END, "\n\nCÓDIGO ENSAMBLADOR (progfte.asm):\n")
        tables_area.insert(tk.END, current_masm_code)
        
        tables_area.insert(tk.END, "\n" + "_" * 70 + "\n")

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
root.state('zoomed')

# --- Frames ---
button_frame = tk.Frame(root, padx=5, pady=5)
button_frame.pack(side=tk.TOP, fill=tk.X)
editor_frame = tk.Frame(root)
console_frame = tk.Frame(root)
tables_frame = tk.Frame(root)

# --- Elementos de la GUI (CORREGIDO: DEFINICIÓN DE BOTONES) ---

run_button = tk.Button(button_frame, text="Ejecutar y Optimizar", font=("Arial", 12), command=run_code, bg="#70dc70", fg="#1e1e1e")
run_button.pack(side=tk.LEFT, padx=(0, 5)) 

show_tables_button = tk.Button(button_frame, text="Información/Cuádruplos (Original y Optimizados)", font=("Arial", 12), command=show_tables_view, bg="#4a7098", fg="white")
show_tables_button.pack(side=tk.LEFT, padx=(0, 5))

back_button = tk.Button(button_frame, text="Volver al Editor", font=("Arial", 12), command=show_editor_view)
back_button.pack(side=tk.LEFT)
back_button.config(state=tk.DISABLED) 

# Área de texto del editor
editor_area = scrolledtext.ScrolledText(
    editor_frame, wrap=tk.WORD, padx=10, pady=10, font=("Courier New", 12), bg="#1e1e1e", fg="#dcdcdc", insertbackground="white"
)
editor_area.pack(fill=tk.BOTH, expand=True)

# Contenido inicial (Ejemplo de prueba)
initial_text = """-- Ejemplo de código TigerPy (con Boleano y Cadena)
Inicio
    Entero a = 10
    Entero b = 5
    Entero c = a + b 
    Entero d = ( a + b ) * 2 
    Entero e = ( 10 * 2 ) + d
    Entero f = c

    Boleano g = True
    Boleano h = False

    Cadena i = "Jeje"
    Cadena j = 'Hola'
     
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