import tkinter as tk
from tkinter import scrolledtext
import re
import os

# Diccionario de Precedencia (Jerarquía de Operadores)
PRECEDENCIA = {
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
        if token not in PRECEDENCIA and token not in [')', '(', '"', "'"]:
            salida_posfija.append(token)
        elif token == '(':
            pila_operadores.append(token)
        elif token in PRECEDENCIA:
            while (pila_operadores and pila_operadores[-1] != '(' and 
                   PRECEDENCIA.get(pila_operadores[-1], 0) >= PRECEDENCIA[token]):
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
            if token not in PRECEDENCIA:
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
            if token not in PRECEDENCIA:
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


# --- FASE DE GENERACIÓN DE CÓDIGO ENSAMBLADOR (MASM) ---

def generar_codigo_ensamblador_masm(cuadruplos_optimizados, variables):
    """
    Genera código ensamblador (MASM) con la corrección para imprimir los nombres literales.
    """
    global current_masm_code
    
    # 1. Recolectar variables y temporales usados en los cuádruplos (lógica simplificada)
    data_section = "\n.DATA\n"
    
    # Variables de soporte para las rutinas de impresión
    data_section += " \tMSJ_SALTO \t DB \t0DH, 0AH, '$' ; Salto de línea\n"
    data_section += " \tMSJ_DELIM \t DB \t' = ', '$'\n"
    data_section += " \tAUX_SALIDA \t DW \t20 DUP(?), '$'\n"
    data_section += " \tCAD_TRUE \t DB \t'True', '$'\n"
    data_section += " \tCAD_FALSE \t DB \t'False', '$'\n"
    
    # Declarar los nombres de las variables como cadenas literales (CORRECCIÓN)
    variable_messages = {}
    for var_name in variables.keys():
        msg_name = f"MSJ_VAR_{var_name.upper()}"
        data_section += f" \t{msg_name:<10} DB \t'{var_name}', '$'\n"
        variable_messages[var_name] = msg_name

    # Declarar TODAS las variables del usuario
    for var_name, info in variables.items():
        var_type = info['tipo']
        initial_value = info['valor']
        
        if var_type in ['Entero', 'Numero', 'Boleano']:
            data_section += f" \t{var_name:<8} \t DW \t0 \t; {var_type}\n"
        elif var_type == 'Cadena':
            if initial_value is not None and not (str(initial_value).startswith(('"', "'"))):
                data_section += f" \t{var_name:<8} \t DB \t'{initial_value}', '$' \t; {var_type}\n"
            else:
                # Reservar espacio, asumiendo una cadena de 255 si no tiene valor inicial asignado en tiempo de compilación
                data_section += f" \t{var_name:<8} \t DB \t255 DUP('$') ; Reservar 255 bytes para Cadena\n"
    
    # --- Generación del cuerpo del código (CODE) ---
    code_body = ""
    for op, arg1, arg2, result in cuadruplos_optimizados:
        arg1_src = str(arg1)
        arg2_src = str(arg2)
        is_string_assignment = variables.get(result, {}).get('tipo') == 'Cadena'

        code_body += f"\n \t; Cuádruplo: ({op}, {arg1_src}, {arg2_src}, {result})\n"
        
        if op == '=':
            if is_string_assignment and not es_constante_numerica(arg1_src):
                 code_body += f" \t; Asignación de Cadena (runtime) no implementada\n"
                 continue

            val = obtener_valor_numerico(arg1_src)
            if val is not None:
                code_body += f" \tMOV {result}, {val}\n"
            else:
                code_body += f" \tMOV AX, {arg1_src}\n \tMOV {result}, AX\n"
        
        elif op in ['+', '-', '*', '/']:
            val1 = obtener_valor_numerico(arg1_src)
            val2 = obtener_valor_numerico(arg2_src)

            if val1 is not None: code_body += f" \tMOV AX, {val1}\n"
            else: code_body += f" \tMOV AX, {arg1_src}\n"

            if val2 is not None: code_body += f" \tMOV BX, {val2}\n"
            else: code_body += f" \tMOV BX, {arg2_src}\n"
            
            if op == '+': code_body += f" \tADD AX, BX\n"
            elif op == '-': code_body += f" \tSUB AX, BX\n"
            elif op == '*': code_body += f" \tIMUL BX\n" 
            elif op == '/': 
                code_body += f" \tMOV DX, 0\n" 
                code_body += f" \tIDIV BX\n"
            
            code_body += f" \tMOV {result}, AX\n"


    # --- 4. Rutinas de Salida de Datos (Impresión) ---
    print_code = "\n \t; --- IMPRESIÓN DE VARIABLES (Verificación) ---\n"
    
    for var_name, info in variables.items():
        var_type = info['tipo']
        msg_name = variable_messages[var_name]
        
        # Imprimir Nombre de la variable
        print_code += f" \t; Imprimir {var_name}\n"
        print_code += f" \tLEA DX, {msg_name}\n \tMOV AH, 09H\n \tINT 21H\n" 
        # Imprimir Delimitador
        print_code += f" \tLEA DX, MSJ_DELIM\n \tMOV AH, 09H\n \tINT 21H\n"
        
        if var_type in ['Entero', 'Numero']:
            print_code += f" \tMOV AX, {var_name}\n \tCALL ESCRIBE_NUM\n"
        elif var_type == 'Boleano':
            print_code += f" \tMOV AX, {var_name}\n \tCMP AX, 1\n \tJE .TRUE_{var_name}\n"
            print_code += f" \tLEA DX, CAD_FALSE\n \tJMP .FIN_BOOL_{var_name}\n"
            print_code += f".TRUE_{var_name}:\n \tLEA DX, CAD_TRUE\n"
            print_code += f".FIN_BOOL_{var_name}:\n \tMOV AH, 09H\n \tINT 21H\n"
        elif var_type == 'Cadena':
            print_code += f" \tLEA DX, {var_name}\n \tMOV AH, 09H\n \tINT 21H\n"
            
        # Salto de línea
        print_code += f" \tLEA DX, MSJ_SALTO\n \tMOV AH, 09H\n \tINT 21H\n"

    # --- Ensamblador Final ---
    masm_template = f"""
.MODEL SMALL
.STACK 100H

{data_section}

.CODE
; --- RUTINA DE IMPRESIÓN DE NÚMEROS ---
ESCRIBE_NUM PROC
\tPUSH AX
\tPUSH BX
\tPUSH CX
\tPUSH DX
\tPUSH SI

\tMOV CX, 0 \t; Contador de dígitos
\tMOV BX, 10 \t; Divisor

.DIV_LOOP:
\tMOV DX, 0 \t; DX:AX para IDIV
\tIDIV BX \t; AX = AX/10, DX = AX%10
\tPUSH DX \t; Poner el residuo (dígito) en la pila
\tINC CX
\tCMP AX, 0 
\tJNE .DIV_LOOP

.PRINT_LOOP:
\tPOP DX \t; Sacar el dígito
\tADD DL, '0' ; Convertir a ASCII
\tMOV AH, 02H ; Función de salida de un carácter
\tINT 21H \t; Imprimir
\tLOOP .PRINT_LOOP

\tPOP SI
\tPOP DX
\tPOP CX
\tPOP BX
\tPOP AX
\tRET
ESCRIBE_NUM ENDP

MAIN PROC
 \t; Inicializar segmento de datos
 \tMOV AX, @DATA
 \tMOV DS, AX

 \t; Código generado a partir de cuádruplos:
{code_body}
{print_code}

 \t; Salir al DOS
 \tMOV AH, 4CH
 \tINT 21H
MAIN ENDP
END MAIN
"""
    current_masm_code = masm_template.strip()
    return current_masm_code

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
            
            # --- MANEJO DE DECLARACIONES/ASIGNACIONES ---
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
                        
                        if (tipo_var in ['Entero', 'Numero']) and any(op in expresion_tokens for op in PRECEDENCIA.keys()):
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

# Variables globales para almacenar los resultados del análisis
current_tokens = []
current_variables = {}
current_errors = []
current_lexemas_depurados = []
current_cuadruplos = []
optimized_cuadruplos = [] 
current_masm_code = ""

def generar_tabla_simbolos_str(tokens, variables):
    simbolos_map = {}
    
    for token in tokens:
        lexema = token['Lexema']
        token_type = token['Token']
        
        # Omitir solo operadores, asignaciones y delimitadores.
        if token_type in ['OPERADOR', 'ASIGNACION', 'DELIMITADOR']:
            continue
            
        # Usar el lexema (o valor para constantes) como clave para asegurar unicidad
        map_key = lexema if token_type not in ['CONSTANTE_NUMERICA', 'CADENA'] else f"{lexema}_{token_type}"
        
        if map_key not in simbolos_map:
            
            # Determinar Categoría/Tipo de Dato
            categoria = "Constante"
            tipo_dato = "N/A"
            
            if lexema in variables:
                categoria = "Variable"
                tipo_dato = variables[lexema]['tipo']
            elif token_type == 'PALABRA_RESERVADA':
                categoria = "Palabra Reservada"
                if lexema in ['Entero', 'Numero', 'Cadena', 'Boleano']:
                    tipo_dato = lexema
                elif lexema in ['True', 'False', 'true', 'false']:
                    tipo_dato = 'Boleano'
                else: # Inicio, Fin
                    categoria = "Estructura"
                    
            elif token_type == 'IDENTIFICADOR':
                categoria = "Identificador (No declarado)"
                
            elif token_type == 'CONSTANTE_NUMERICA':
                tipo_dato = 'Numérico'
            elif token_type == 'CONSTANTE_BOOLEANA':
                tipo_dato = 'Boleano'
            elif token_type == 'CADENA':
                tipo_dato = 'Cadena'

            simbolos_map[map_key] = {
                'Linea': token['Linea'], 
                'Lexema': lexema,
                'Token': token_type, 
                'Referencia': token['Referencia'], 
                'Tipo': tipo_dato,
                'Categoria': categoria,
            }

    output = "TABLA DE SÍMBOLOS (SEMÁNTICA)\n"
    # Ajustado a 3 columnas: Nombre del Símbolo, Tipo de Dato, Categoría/Clase
    header_line1 = f"{'Nombre del Símbolo':<25} {'Tipo de Dato':<15} {'Categoría/Clase':<20}\n"
    output += header_line1
    output += "-" * 60 + "\n" # Separador ajustado
    
    for sim_info in simbolos_map.values():
        # Usamos sim_info['Lexema'] como 'Nombre del Símbolo'
        output += (
            f"{sim_info['Lexema']:<25} "
            f"{sim_info['Tipo']:<15} "
            f"{sim_info['Categoria']:<20}\n"
        )
        
    return output

def generar_tabla_tokens_str(tokens):
    output = "TABLA DE TOKENS (LÉXICA)\n"
    # Ajustado a 3 columnas: Línea, Lexema (Secuencia de Caracteres), Tipo de Token
    header_line1 = f"{'Línea':<8} {'Lexema (Secuencia de Caracteres)':<35} {'Tipo de Token':<25}\n"
    output += header_line1
    output += "-" * 68 + "\n" # Separador ajustado
    for token in tokens:
        output += (
            f"{token['Linea']:<8} "
            f"{token['Lexema']:<35} "
            f"{token['Token']:<25}\n" # Se omite la columna 'Referencia'
        )
    return output

def generar_tabla_variables_str(variables):
    output = f"{'Variable':<15} {'Tipo':<12} {'Asignada':<10} {'Valor (Final)':<25}\n"
    output += "-" * 65 + "\n"
    for var_name, info in variables.items():
        valor_str = str(info['valor']) if info['valor'] is not None else 'None'
        output += f"{var_name:<15} {info['tipo']:<12} {str(info['asignada']):<10} {valor_str:<25}\n"
    return output

def generar_tabla_cuadruplos_str(cuadruplos):
    output = f"{'No.':<5} {'Operador':<15} {'Op1':<10} {'Op2':<10} {'Resultado':<10}\n"
    output += "-" * 65 + "\n"
    if not cuadruplos:
        return output + "No se generaron cuádruplos para expresiones."
        
    for i, (op, arg1, arg2, result) in enumerate(cuadruplos):
        output += f"{i:<5} {op:<15} {str(arg1):<10} {str(arg2):<10} {str(result):<10}\n"
    return output

def generar_codigo_depurado_str(lexemas_depurados):
    return ''.join(lexemas_depurados)


# --- FUNCIONES DE RESALTADO DE SINTAXIS ---

def resaltar_sintaxis(event=None):
    """
    Función que aplica el resaltado de sintaxis en el editor_area.
    """
    global editor_area
    
    # Eliminar todas las etiquetas de resaltado existentes
    for tag in editor_area.tag_names():
        if tag.startswith('highlight_'):
            editor_area.tag_remove(tag, "1.0", tk.END)

    code = editor_area.get("1.0", tk.END)
    lines = code.split('\n')
    
    # Definiciones de patrones y etiquetas
    patterns = {
        'highlight_comentario': (r'(?m)^--.*', '#7F848E'), # Gris para comentarios (al inicio de línea)
        'highlight_tipodato': (r'\b(Entero|Numero|Cadena|Boleano)\b', '#61AFEF'), # Azul para tipos de datos
        'highlight_reservada': (r'\b(Inicio|Fin|True|False)\b', '#C678DD'), # Morado para palabras reservadas
        'highlight_operador': (r'[+\-*/=]', '#E06C75'), # Rojo para operadores y asignación
        'highlight_string': (r'(\".*?\")|(\'.*?\')', '#98C379'), # Verde claro para cadenas
        'highlight_number': (r'\b\d+(\.\d+)?\b', '#D19A66'), # Naranja para números
        'highlight_identificador': (r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', '#98C379') # Gris para identificadores (se corrige si es reservada)
    }

    # Aplicar tags en cada línea
    for i, line in enumerate(lines, 1):
        line_start = f"{i}.0"
        line_end = f"{i}.{len(line)}"
        
        # 1. Aplicar etiquetas para Identificadores, Números, Strings, Operadores, etc.
        # Recorremos los patrones en orden de importancia (de más específico a menos)
        for tag, (pattern, color) in patterns.items():
            # Configurar el tag si aún no existe
            if tag not in editor_area.tag_names():
                editor_area.tag_config(tag, foreground=color)

            # Buscar coincidencias en la línea
            for match in re.finditer(pattern, line):
                start_index = f"{i}.{match.start()}"
                end_index = f"{i}.{match.end()}"

                # Si es un identificador, lo marcamos (la lógica posterior lo sobreescribe si es TD o PR)
                if tag == 'highlight_identificador':
                    # No resaltar identificadores si son palabras clave ya que están cubiertas por otros tags.
                    if match.group() not in ['Entero', 'Numero', 'Cadena', 'Boleano', 'Inicio', 'Fin', 'True', 'False']:
                        editor_area.tag_add(tag, start_index, end_index)
                else:
                    editor_area.tag_add(tag, start_index, end_index)
        
# --- FUNCIONES DE CONTROL DE LA GUI ---

def run_code():
    global current_tokens, current_variables, current_errors, current_lexemas_depurados, current_cuadruplos, optimized_cuadruplos, current_masm_code
    
    code_to_compile = editor_area.get("1.0", tk.END).strip()
    
    # 0. Resaltar la sintaxis antes de compilar (por si no se hizo al escribir)
    resaltar_sintaxis()

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

        if current_errors:
            console_area.insert(tk.END, "[Errores de Sintaxis/Semántica]:\n", "error_tag")
            for error in current_errors:
                console_area.insert(tk.END, f" \t- {error}\n", "error_tag")
        else:
            console_area.insert(tk.END, f">>> Se ha compleado el compilado.\n", "output_tag")
            console_area.insert(tk.END, ">>> No se encontraron errores.\n", "output_tag")
            console_area.insert(tk.END, ">>> Archivo .asm generado con éxito.\n", "output_tag")
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
        # tables_area.insert(tk.END, generar_tabla_simbolos_str(current_tokens, current_variables))
        
        # tables_area.insert(tk.END, "\n\n" + "_" * 70 + "\n")

        # tables_area.insert(tk.END, generar_tabla_tokens_str(current_tokens))
        
        # tables_area.insert(tk.END, "\n" + "_" * 70 + "\n")
        
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
    
    # Asegurarse de que el resaltado se aplique al volver a la vista
    resaltar_sintaxis()

    show_tables_button.config(state=tk.NORMAL)
    run_button.config(state=tk.NORMAL)
    back_button.config(state=tk.DISABLED)
    
# --- FUNCIONES DE MANEJO DE VENTANA (Mover y Cerrar) ---
def start_move(event):
    """Guarda la posición inicial del clic para arrastrar la ventana."""
    root.x = event.x
    root.y = event.y

def do_move(event):
    """Mueve la ventana a la nueva posición del cursor."""
    deltax = event.x - root.x
    deltay = event.y - root.y
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry(f"+{x}+{y}")
# --------------------------------------------------------------------------

# --- Configuración de la ventana principal (Interfaz Gráfica) ---
root = tk.Tk()
root.title("Compilador TigerPy")
root.state('zoomed')

# 1. Eliminar la barra de título nativa para control manual
root.overrideredirect(True) 

root.config(bg="#282C34") # Fondo principal (gris oscuro)

# --- Frames ---
button_frame = tk.Frame(root, padx=5, pady=5, bg="#282C34")
button_frame.pack(side=tk.TOP, fill=tk.X)

# 2. Asignar eventos de movimiento al button_frame para arrastrar la ventana
button_frame.bind("<ButtonPress-1>", start_move)
button_frame.bind("<B1-Motion>", do_move)

BG = "#282C34"  # Color de fondo gris oscuro para los frames
editor_frame = tk.Frame(root, bg=BG)
console_frame = tk.Frame(root, bg=BG)
tables_frame = tk.Frame(root, bg=BG)

# --- Estilos Comunes ---
FONT = "Fira Code"
button_style = {
    "font": (FONT, 13, "bold"), 
    "relief": tk.FLAT,           # Botones planos (sin borde 3D)
    "bd": 0,                      # Ancho de borde cero
    "highlightthickness": 0       # Elimina el borde de enfoque
}

text_area_style = {
    "font": (FONT, 12),
    "bg": "#21252B",              # Fondo muy oscuro para el editor/consola
    "insertbackground": "white", 
    "relief": tk.FLAT,           # Área de texto plana
    "highlightthickness": 0,      # Elimina el contorno blanco de enfoque
    "padx": 10, 
    "pady": 10,
}

# --- Botones de Control ---
run_button = tk.Button(
    button_frame, 
    text="Compilar", 
    command=run_code, 
    bg="#61AFEF",               # Azul vibrante
    fg="white", 
    activebackground="#509ade", 
    activeforeground="white",
    **button_style
)
run_button.pack(side=tk.LEFT, padx=(0, 5)) 

show_tables_button = tk.Button(
    button_frame, 
    text="Información", 
    command=show_tables_view, 
    bg="#98C379",               # Verde sutil
    fg="#1e1e1e",
    activebackground="#82b36b",
    activeforeground="#1e1e1e",
    **button_style
)
show_tables_button.pack(side=tk.LEFT, padx=(0, 5))

back_button = tk.Button(
    button_frame, 
    text="Regresar", 
    command=show_editor_view,
    bg="#5C6370", 
    fg="white",
    **button_style
)
back_button.pack(side=tk.LEFT)
back_button.config(state=tk.DISABLED) 

# 3. Botón de Cierre (X)
close_button = tk.Button(
    button_frame,
    text="X",
    font=(FONT, 14, "bold"),
    command=root.destroy,           # Cierra la ventana y termina el proceso
    bg="#E06C75",                   # Rojo coral (color de error/cierre)
    fg="white",
    activebackground="#C25A63",
    activeforeground="white",
    relief=tk.FLAT,
    bd=0,
    width=5, 
    highlightthickness=0
)
close_button.pack(side=tk.RIGHT)

# --- Áreas de Texto ---

# Editor
editor_area = scrolledtext.ScrolledText(
    editor_frame, 
    wrap=tk.WORD, 
    fg="#ABB2BF",               # Color base del texto (gris claro)
    **text_area_style
)

initial_text = """-- Ejemplo de la sintaxis de TigerPy
Inicio
    Entero edad = 100
    Cadena nombre = "Tigre Grr"
    Boleano esAdulto = True
    Entero resultado = edad + 20 * 2
Fin"""

editor_area.pack(fill=tk.BOTH, expand=True)
editor_area.insert(tk.END,initial_text)
# 4. Enlazar el evento de tecleo al editor para actualizar el resaltado en tiempo real
editor_area.bind('<KeyRelease>', resaltar_sintaxis)
# Aplicar resaltado inicial
resaltar_sintaxis()


# Consola
console_area = scrolledtext.ScrolledText(
    console_frame, 
    wrap=tk.WORD, 
    height=10, 
    fg="#56B6C2",               
    state=tk.DISABLED,
    **text_area_style
)
console_area.pack(fill=tk.BOTH, expand=True)

# Área de Tablas/Ensamblador
tables_area = scrolledtext.ScrolledText(
    tables_frame, 
    wrap=tk.WORD, 
    fg="#ABB2BF", 
    state=tk.DISABLED,
    **text_area_style
)
tables_area.pack(fill=tk.BOTH, expand=True)

# Tags para colorear la salida y los errores en la consola
console_area.tag_configure("output_tag", foreground="#4BE755") # Verde para mensajes de éxito
console_area.tag_configure("error_tag", foreground="#E06C75") # Rojo para errores
console_area.tag_configure("prompt_tag", foreground="#56B6C2")

# Iniciar con la vista del editor
editor_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
console_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)

# --- Bucle principal ---
root.mainloop()