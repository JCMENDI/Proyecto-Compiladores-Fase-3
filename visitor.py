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
    def _init_(self):
        self.memory = {}
        self.functions = {}
        self.output_code = []
        self.current_function = None
        self.indent_level = 0

    def write_output(self, filename="output.py"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# Código generado automáticamente\n")
            f.write("\n".join(self.output_code))

    def add_code_line(self, line):
        indent = "    " * self.indent_level
        self.output_code.append(f"{indent}{line}")

    def visitPrograma(self, ctx):
        self.output_code = []
        self.visit(ctx.bloque())
        self.write_output()
        return None

    def visitBloque(self, ctx):
        if ctx.declaraciones():
            self.visit(ctx.declaraciones())
        self.visit(ctx.compound_statement())
        return None

    def visitDeclaraciones(self, ctx):
        for decl in ctx.declaracion():
            self.visit(decl)

    def visitDeclaracion(self, ctx):
        return self.visitChildren(ctx)

    def visitVar_declaracion(self, ctx):
        var_name = ctx.ID().getText()
        self.memory[var_name] = None
        if not self.current_function:  # Solo variables globales
            self.add_code_line(f"{var_name} = None")
        return None
    
    def visitFuncion_declaracion(self, ctx):
        func_name = ctx.ID().getText()
        self.functions[func_name] = ctx
        
        # Guardar estado actual
        old_memory = self.memory.copy()
        old_output = self.output_code
        old_indent = self.indent_level
        
        # Configurar para función
        self.output_code = []
        self.memory = {}
        self.current_function = func_name
        self.indent_level = 1

        # Procesar parámetros
        parametros = []
        if ctx.lista_parametros():
            for p in ctx.lista_parametros().parametro():
                param_name = p.ID().getText()
                parametros.append(param_name)
                self.memory[param_name] = None

        # Generar función
        func_header = f"def {func_name}({', '.join(parametros)}):"
        old_output.append(func_header)

        # Procesar cuerpo
        self.visit(ctx.bloque())

        # Restaurar estado
        old_output.extend(self.output_code)
        self.output_code = old_output
        self.memory = old_memory
        self.current_function = None
        self.indent_level = old_indent
        return None

    def visitCompound_statement(self, ctx):
        if ctx.lista_sentencias():
            self.visit(ctx.lista_sentencias())
        return None

    def visitLista_sentencias(self, ctx):
        for stmt in ctx.sentencia():
            self.visit(stmt)
        return None

    def visitSentencia(self, ctx):
        return self.visitChildren(ctx)

    def visitAsignacion(self, ctx):
        var_name = ctx.ID().getText()
        value = self.visit(ctx.expresion())
        self.add_code_line(f"{var_name} = {value}")
        return value

    def visitSentencia_io(self, ctx):
        if ctx.getChild(0).getText() == 'PRINTLN':
            expr = ctx.getChild(2)
            value = self.visit(expr)
            # Imprimir la variable, no el valor directamente
            self.add_code_line(f"print({expr.getText()})")
        elif ctx.getChild(0).getText() == 'READLN':
            var_name = ctx.getChild(2).getText()
            self.add_code_line(f"{var_name} = int(input())")
            self.memory[var_name] = 0
        return None

    def visitSentencia_return(self, ctx):
        value = self.visit(ctx.expresion())
        self.add_code_line(f"return {value}")
        return value

    def visitLlamada_procedimiento(self, ctx):
        func_name = ctx.ID().getText()
        if func_name not in self.functions:
            print(f"ERROR: Función {func_name} no definida")
            return "None"

        args = []
        if ctx.lista_argumentos():
            for expr in ctx.lista_argumentos().expresion():
                args.append(self.visit(expr))
        
        call_code = f"{func_name}({', '.join(args)})"
        
        # Solo generar línea si no es parte de otra expresión
        parent_ctx = ctx.parentCtx
        while hasattr(parent_ctx, 'parentCtx'):
            parent_ctx = parent_ctx.parentCtx
            if isinstance(parent_ctx, (MiCompiladorParser.AsignacionContext, 
                                    MiCompiladorParser.Sentencia_returnContext,
                                    MiCompiladorParser.ExpresionContext)):
                return call_code
        
        self.add_code_line(call_code)
        return call_code
    
    def visitSentencia_while(self, ctx):
        condicion = self.visit(ctx.expresion())
        # Asegurarnos que la condición es correcta para Python
        condicion_python = condicion.replace('=', '==').replace('<>', '!=')
        
        # Generar código del while
        self.add_code_line(f"while {condicion_python}:")
        self.indent_level += 1
        self.visit(ctx.sentencia())
        self.indent_level -= 1
        return None