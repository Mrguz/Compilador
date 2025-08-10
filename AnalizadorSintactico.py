import re  # Importamos el módulo de expresiones regulares para leer el archivo .tok
import sys
import io

# -------------------- NODO AST --------------------
class ASTNode:
    """
    Clase para representar un nodo del Árbol de Sintaxis Abstracta (AST).
    Cada nodo puede tener un valor, tipo de token, hijos izquierdo y derecho, y número de línea.
    """
    def __init__(self, value, left=None, right=None, line=None, token_type=None):
        self.value = value            # Valor del nodo (ej. '+', '=', 'id', '5')
        self.token_type = token_type  # Tipo de token (ej. SUMA, IDENTIFICADOR)
        self.left = left              # Subárbol izquierdo
        self.right = right            # Subárbol derecho
        self.line = line              # Número de línea del nodo

    def to_tree_string(self, prefix='', is_tail=True):
        """
        Devuelve una representación en forma de árbol del nodo y sus hijos.
        """
        node_text = f"Token: {self.token_type}, {self.value}" if self.token_type else str(self.value)
        result = prefix + ('└── ' if is_tail else '├── ') + node_text + '\n'
        children = [child for child in (self.left, self.right) if child]
        for i, child in enumerate(children):
            is_last = i == (len(children) - 1)
            new_prefix = prefix + ('    ' if is_tail else '│   ')
            result += child.to_tree_string(new_prefix, is_last)
        return result


# -------------------- PARSER --------------------
class Parser:
    """
    Clase para realizar el análisis sintáctico sobre una lista de tokens y construir árboles AST.
    """
    def __init__(self, tokens):
        self.tokens = tokens          # Lista de tokens leídos desde el archivo .tok
        self.index = 0                # Índice actual en la lista de tokens
        self.ast_list = []            # Lista de árboles AST generados
        self.errors = []              # Lista de errores de sintaxis encontrados
        self.line_reported = set()    # Conjunto de líneas que ya reportaron error (para evitar repetidos)

    def current(self):
        """Devuelve el token actual o None si ya no hay más tokens."""
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def advance(self):
        """Avanza al siguiente token."""
        self.index += 1

    def match(self, expected_type):
        """
        Compara si el token actual es del tipo esperado y avanza si coincide.
        Devuelve el token si hubo coincidencia o None en caso contrario.
        """
        token = self.current()
        if token and token['type'] == expected_type:
            self.advance()
            return token
        return None

    def parse_all(self):
        """
        Analiza todos los tokens. Intenta construir árboles para todas las expresiones
        que comiencen con un identificador (asignaciones).
        """
        while self.index < len(self.tokens):
            token = self.current()
            if not token:
                break

            if token['type'] == 'IDENTIFICADOR':
                start_line = token['line']
                try:
                    node = self.try_parse_assignment(start_line)
                    if node:
                        self.ast_list.append(node)
                        continue
                except SyntaxError as e:
                    # Registrar error si aún no se ha reportado en esa línea
                    if start_line not in self.line_reported:
                        self.errors.append(f"Línea {start_line}: Error de sintaxis: {e}")
                        self.line_reported.add(start_line)
                    self.skip_line(start_line)
                    continue

            # Si no es una asignación, saltar toda la línea
            self.skip_line(token['line'])

    def skip_line(self, line):
        """Avanza el índice hasta salir de la línea actual."""
        while self.current() and self.current()['line'] == line:
            self.advance()

    def try_parse_assignment(self, expected_line):
        """
        Intenta reconocer una asignación de la forma: id = expresión.
        Retorna el nodo raíz del árbol si se pudo construir correctamente.
        """
        start_index = self.index
        id_token = self.match('IDENTIFICADOR')
        igual_token = self.match('IGUAL')

        # Asegurarse de que la expresión esté en la misma línea
        if id_token and igual_token and self.current() and self.current()['line'] == expected_line:
            expr = self.expr(expected_line)

            # Verificar que no haya tokens sobrantes en la línea
            while self.current() and self.current()['line'] == expected_line:
                raise SyntaxError(f"Token inesperado: '{self.current()['value']}' después de la expresión")

            # Construir nodo '=' con el identificador a la izquierda y la expresión a la derecha
            return ASTNode('=',
                           ASTNode(id_token['value'], token_type=id_token['type']),
                           expr,
                           line=expected_line,
                           token_type=igual_token['type'])

        # Si falla el patrón esperado, restaurar el índice original
        self.index = start_index
        return None

    def expr(self, expected_line):
        """
        Analiza una expresión con operadores + y -.
        """
        node = self.term(expected_line)
        while self.current() and self.current()['type'] in ('SUMA', 'RESTA') and self.current()['line'] == expected_line:
            op_token = self.current()
            self.advance()

            # Validar que haya un operando a la derecha
            if not self.current() or self.current()['line'] != expected_line:
                raise SyntaxError(f"Falta operando derecho para operador '{op_token['value']}'")

            right = self.term(expected_line)
            node = ASTNode(op_token['value'], node, right, token_type=op_token['type'])
        return node

    def term(self, expected_line):
        """
        Analiza términos con operadores * y /.
        """
        node = self.factor(expected_line)
        while self.current() and self.current()['type'] in ('MULTIPLICACION', 'DIVISION') and self.current()['line'] == expected_line:
            op_token = self.current()
            self.advance()

            # Validar que haya un operando a la derecha
            if not self.current() or self.current()['line'] != expected_line:
                raise SyntaxError(f"Falta operando derecho para operador '{op_token['value']}'")

            right = self.factor(expected_line)
            node = ASTNode(op_token['value'], node, right, token_type=op_token['type'])
        return node

    def factor(self, expected_line):
        """
        Analiza factores: constantes, identificadores, o subexpresiones entre paréntesis.
        """
        tok = self.current()
        if not tok:
            raise SyntaxError("Expresión incompleta")

        if tok['line'] != expected_line:
            raise SyntaxError("Token fuera de línea esperada")

        if tok['type'] == 'PAREN_IZQ':
            self.advance()
            node = self.expr(expected_line)
            if not self.match('PAREN_DER'):
                raise SyntaxError("Falta paréntesis de cierre ')'")
            return node
        elif tok['type'] == 'PAREN_DER':
            raise SyntaxError("Paréntesis de cierre inesperado ')'")
        elif tok['type'] in ('IDENTIFICADOR', 'CONSTANTE'):
            self.advance()
            return ASTNode(tok['value'], token_type=tok['type'])
        else:
            raise SyntaxError(f"Token inesperado: '{tok['value']}'")


# -------------------- FUNCIONES AUXILIARES --------------------
def cargar_tokens_desde_tok(archivo):
    """
    Carga tokens desde un archivo .tok y los convierte en una lista de diccionarios.
    Cada línea del archivo debe tener: Renglón: <número> Lexema: <valor> Token: <tipo>
    """
    tokens = []
    patron = r'Renglón:\s+(\d+)\s+Lexema:\s+(.*?)\s+Token:\s+(\w+)'
    with open(archivo, 'r', encoding='utf-8') as f:
        for linea in f:
            match = re.match(patron, linea)
            if match:
                renglon, lexema, tipo = match.groups()
                tokens.append({
                    'line': int(renglon),
                    'value': lexema.strip(),
                    'type': tipo.strip()
                })
    return tokens

# Establecer stdout a UTF-8 explícitamente (para evitar errores con subprocess en Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# -------------------- PROGRAMA PRINCIPAL --------------------
if __name__ == '__main__':
    archivo_tok = 'progfte.tok'  # Nombre del archivo de entrada .tok
    tokens = cargar_tokens_desde_tok(archivo_tok)

    parser = Parser(tokens)
    parser.parse_all()

    print("\nÁrboles sintácticos generados:")
    # Imprimir los árboles sintácticos generados
    if parser.ast_list:
        for i, ast in enumerate(parser.ast_list, 1):
            print(f"\nÁrbol {i} (línea {ast.line}):")
            print(ast.to_tree_string())

    # Imprimir errores si los hay
    if parser.errors:
        print("\n❌ Errores sintácticos encontrados:")
        for err in parser.errors:
            print(" ", err)
    elif not parser.ast_list:
        print("No se encontraron expresiones aritméticas válidas.")

print("\n")