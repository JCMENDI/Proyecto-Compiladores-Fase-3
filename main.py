from antlr4 import *
from MiCompiladorLexer import MiCompiladorLexer
from MiCompiladorParser import MiCompiladorParser
from visitor import EvalVisitor, MiErrorListener
import subprocess

def main():
    input_file = "input2.txt"  # Tu archivo con código fuente personalizado

    with open(input_file, 'r', encoding='utf-8') as f:
        input_code = f.read()

    input_stream = InputStream(input_code)
    lexer = MiCompiladorLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = MiCompiladorParser(stream)

    error_listener = MiErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)

    tree = parser.programa()

    if error_listener.hubo_error:
        print("Error de sintaxis. No se generó el archivo output.py")
        return

    visitor = EvalVisitor()
    visitor.visit(tree)
    visitor.write_output()  # Esto guarda el código traducido en output.py

    print("✅ Traducción completada. Archivo generado: output.py")
    
    # OPCIONAL: Ejecutar el archivo Python generado
    print("▶ Ejecutando output.py...\n")
    subprocess.run(["python", "output.py"], check=False)

if __name__ == '__main__':
    main()
