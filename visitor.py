from MiCompiladorVisitor import MiCompiladorVisitor
from MiCompiladorParser import MiCompiladorParser
from antlr4.error.ErrorListener import ErrorListener

class MiErrorListener(ErrorListener):
    def __init__(self):
        super(MiErrorListener, self).__init__()
        self.hubo_error = False

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print(f"Error de sintaxis en la línea {line}, columna {column}: {msg}")
        self.hubo_error = True

class EvalVisitor(MiCompiladorVisitor):
    def __init__(self):
        self.memory = {}
        self.functions = {}
        self.output_code = []  # Código traducido a Python

    def write_output(self, filename="output.py"):
        with open(filename, "w", encoding="utf-8") as f:
            for line in self.output_code:
                f.write(line + "\n")

    def visitPrograma(self, ctx):
        print("Visit: programa")
        result = self.visit(ctx.bloque())
        self.write_output()
        return result

    def visitBloque(self, ctx):
        print("Visit: bloque")
        if ctx.declaraciones():
            self.visit(ctx.declaraciones())
        return self.visit(ctx.compound_statement())

    def visitDeclaraciones(self, ctx):
        print("Visit: declaraciones")
        for decl in ctx.declaracion():
            self.visit(decl)

    def visitDeclaracion(self, ctx):
        print("Visit: declaracion")
        return self.visitChildren(ctx)

    def visitVar_declaracion(self, ctx):
        print("Visit: var_declaracion")
        var_name = ctx.ID().getText()
        tipo = ctx.tipo().getText()
        self.memory[var_name] = None
        self.output_code.append(f"{var_name} = None")
        print(f"Declared variable: {var_name} of type {tipo}")
        if ctx.var_declaracion():
            self.visit(ctx.var_declaracion())

    def visitFuncion_declaracion(self, ctx):
        print("Visit: funcion_declaracion")
        func_name = ctx.ID().getText()
        self.functions[func_name] = ctx
        print(f"Declared function: {func_name}")


    def visitCompound_statement(self, ctx):
        print("Visit: compound_statement")
        if ctx.lista_sentencias():
            self.visit(ctx.lista_sentencias())

    def visitLista_sentencias(self, ctx):
        print("Visit: lista_sentencias")
        for stmt in ctx.sentencia():
            result = self.visit(stmt)
            if isinstance(result, dict) and result.get("return") is not None:
                return result

    def visitSentencia(self, ctx):
        print("Visit: sentencia")
        return self.visitChildren(ctx)

    def visitAsignacion(self, ctx):
        print("Visit: asignacion")
        var_name = ctx.ID().getText()
        if var_name not in self.memory:
            print(f"ERROR: Variable {var_name} no declarada")
            return
        value = self.visit(ctx.expresion())
        if isinstance(value, dict) and "return" in value:
            value = value["return"]
        self.memory[var_name] = value
        self.output_code.append(f"{var_name} = {value if isinstance(value, (int, float, str)) else var_name}")
        print(f"Assigned: {var_name} := {value}")
        return value

    def visitSentencia_io(self, ctx):
        print("Visit: sentencia_io")
        if ctx.getChild(0).getText() == 'PRINTLN':
            expr = ctx.getChild(2)
            value = self.memory.get(expr.getText()) if expr.getText() in self.memory else self.visit(expr)
            self.output_code.append(f"print({expr.getText()})")
            print(f"PRINTLN: {value}")
        elif ctx.getChild(0).getText() == 'READLN':
            var_name = ctx.getChild(2).getText()
            val = input(f"READLN {var_name}: ")
            self.memory[var_name] = int(val) if val.isdigit() else val
            self.output_code.append(f"{var_name} = input()")
            print(f"READ value for {var_name}: {self.memory[var_name]}")

    def visitSentencia_if(self, ctx):
        print("Visit: sentencia_if")
        condition = self.visit(ctx.expresion())
        cond_text = ctx.expresion().getText().replace("=", "==")
        if condition:
            print("Condition is True")
            self.output_code.append(f"if {cond_text}:")
            self.visit(ctx.sentencia(0))
        elif ctx.sentencia(1):
            print("Condition is False, executing ELSE")
            self.output_code.append(f"else:")
            self.visit(ctx.sentencia(1))

    def visitSentencia_while(self, ctx):
        print("Visit: sentencia_while")
        cond_text = ctx.expresion().getText().replace("=", "==")
        self.output_code.append(f"while {cond_text}:")
        while self.visit(ctx.expresion()):
            print("WHILE condition True, executing loop body")
            result = self.visit(ctx.sentencia())
            if isinstance(result, dict) and result.get("return") is not None:
                return result

    def visitSentencia_return(self, ctx):
        print("Visit: sentencia_return")
        value = self.visit(ctx.expresion())
        self.output_code.append(f"    return {value}")
        if isinstance(value, dict) and "return" in value:
            value = value["return"]
        print(f"RETURN value: {value}")
        return {"return": value}

    def visitLlamada_procedimiento(self, ctx):
        print("Visit: llamada_procedimiento")
        func_name = ctx.ID().getText()

        if func_name not in self.functions:
            print(f"ERROR: Function {func_name} not defined")
            return None

        func_ctx = self.functions[func_name]
        old_memory = self.memory.copy()

        # Obtener listas de parámetros y argumentos
        param_list = func_ctx.lista_parametros()
        arg_list = ctx.lista_argumentos()

        params = param_list.parametro() if param_list else []
        args = arg_list.expresion() if arg_list else []

        if len(params) != len(args):
            print(f"ERROR: {func_name} esperaba {len(params)} argumentos pero se pasaron {len(args)}")
            return None

        # Asignar valores de argumentos a parámetros
        for p, a in zip(params, args):
            param_name = p.ID().getText()
            arg_value = self.visit(a)
            self.memory[param_name] = arg_value
            print(f"Function param {param_name} := {arg_value}")

        # Ejecutar el cuerpo de la función
        result = self.visit(func_ctx.bloque())

        # Restaurar la memoria anterior
        self.memory = old_memory

        if isinstance(result, dict) and "return" in result:
            return result["return"]
        return None 

    def visitExpresion(self, ctx):
        print("Visit: expresion")
        if ctx.operador_relacional():
            left = self.visit(ctx.expresion_simple(0))
            right = self.visit(ctx.expresion_simple(1))
            op = ctx.operador_relacional().getText()
            result = self.apply_op(op, left, right)
            print(f"Evaluated: {left} {op} {right} = {result}")
            return result
        elif ctx.expresion_simple():
            return self.visit(ctx.expresion_simple(0))
        else:
            return self.visitChildren(ctx)

    def visitExpresion_simple(self, ctx):
        print("Visit: expresion_simple")
        result = self.visit(ctx.termino(0))
        for i in range(1, len(ctx.termino())):
            op = ctx.operador_aditivo(i - 1).getText()
            right = self.visit(ctx.termino(i))
            result = self.apply_op(op, result, right)
            print(f"Evaluated (aditivo): {result}")
        return result

    def visitTermino(self, ctx):
        print("Visit: termino")
        result = self.visit(ctx.factor(0))
        for i in range(1, len(ctx.factor())):
            op = ctx.operador_multiplicativo(i - 1).getText()
            right = self.visit(ctx.factor(i))
            result = self.apply_op(op, result, right)
            print(f"Evaluated (multiplicativo): {result}")
        return result

    def visitFactor(self, ctx):
        print("Visit: factor")
        text = ctx.getText()
        if text.startswith('"') and text.endswith('"'):
            value = text.strip('"')
            print(f"Value: {value}")
            return value
        if ctx.INT():
            value = int(ctx.INT().getText())
            print(f"Value: {value}")
            return value
        if ctx.FLOAT():
            value = float(ctx.FLOAT().getText())
            print(f"Value: {value}")
            return value
        if ctx.ID():
            var_name = ctx.ID().getText()
            if var_name not in self.memory:
                print(f"ERROR: Variable {var_name} no declarada")
                return None
            value = self.memory.get(var_name, None)
            print(f"Variable value: {var_name} = {value}")
            return value
        if ctx.expresion():
            return self.visit(ctx.expresion())
        if ctx.llamada_procedimiento():
            return self.visit(ctx.llamada_procedimiento())
        return self.visitChildren(ctx)

    def apply_op(self, op, left, right):
        if op == '+': return left + right
        if op == '-': return left - right
        if op == '*': return left * right
        if op == '/': return left / right
        if op == '=': return left == right
        if op == '<>': return left != right
        if op == '<': return left < right
        if op == '<=': return left <= right
        if op == '>': return left > right
        if op == '>=': return left >= right
