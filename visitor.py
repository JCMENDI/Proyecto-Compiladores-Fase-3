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