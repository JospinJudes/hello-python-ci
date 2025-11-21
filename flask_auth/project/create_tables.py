# create_tables.py — safe importer pour flask_auth.project
import importlib
import sys
import os

# s'assurer que la racine du repo est dans le path (utile si exécuté depuis la racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

MODULE = 'flask_auth.project'

def main():
    try:
        pkg = importlib.import_module(MODULE)
    except Exception as e:
        print(f"Erreur en important le package {MODULE}: {e}")
        raise

    # essayer de récupérer db et app/create_app depuis le package
    db = getattr(pkg, 'db', None)
    app = getattr(pkg, 'app', None)
    create_app = getattr(pkg, 'create_app', None)

    # si create_app existe, appelle-la pour obtenir l'app
    if callable(create_app):
        try:
            app = create_app()
        except Exception as e:
            print("Erreur lors de l'appel à create_app():", e)
            raise

    if app is None or db is None:
        # tenter une importation relative alternative (fallback)
        try:
            # exemple: from flask_auth.project import __init__ as mod; mod.create_app()/mod.db
            mod = importlib.import_module(MODULE + '.__init__')
            db = db or getattr(mod, 'db', None)
            if app is None and hasattr(mod, 'create_app'):
                app = mod.create_app()
        except Exception:
            pass

    if app is None or db is None:
        raise RuntimeError("Impossible de trouver 'app' et/ou 'db' dans flask_auth.project. Vérifie __init__.py")

    with app.app_context():
        db.create_all()
        print("Tables created successfully")

if __name__ == '__main__':
    main()
