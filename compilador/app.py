"""
Punto de entrada de la aplicación de escritorio.
Inicia el servidor Flask en segundo plano y abre
una ventana nativa con pywebview apuntando a localhost.
Funciona 100% offline — no requiere internet.
"""
import threading
import sys
import os

# Agrega el directorio raíz al path para que los imports de backend funcionen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.server import app as flask_app


def start_flask():
    # En Replit usamos 0.0.0.0; en desktop local basta con localhost
    host = '0.0.0.0' if os.environ.get('REPL_ID') else 'localhost'
    flask_app.run(host=host, port=5000, debug=False, use_reloader=False)


def main():
    # Arranca Flask en un hilo daemon (muere cuando cierra la ventana)
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()

    try:
        import webview
        window = webview.create_window(
            'Compilador — Semestre 5',
            'http://localhost:5000',
            width=1300,
            height=820,
            background_color='#000000'
        )
        webview.start()
    except Exception:
        print("pywebview no disponible — abre http://localhost:5000 en tu navegador")
        t.join()  # Mantiene vivo el proceso


if __name__ == '__main__':
    main()
