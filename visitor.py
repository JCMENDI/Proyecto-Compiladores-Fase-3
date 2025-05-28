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