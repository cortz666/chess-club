"""
Chess Atelier · Club de Aperturas
Aplicación web dinámica (Flask) con base de datos.
- Local: SQLite (archivo club.db)
- Producción (Render): PostgreSQL mediante la variable de entorno DATABASE_URL
"""
import os
import re
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-clave-cambiar")

DATABASE_URL = os.environ.get("DATABASE_URL")
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
    import psycopg2.extras

NIVELES = ["Principiante", "Intermedio", "Avanzado"]


# ---------------------------------------------------------------- Base de datos
def get_conn():
    if USE_PG:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "club.db"))
    conn.row_factory = sqlite3.Row
    return conn


def q(sql):
    """Las consultas se escriben con %s; SQLite usa ?."""
    return sql if USE_PG else sql.replace("%s", "?")


def query(sql, params=(), one=False, commit=False):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(q(sql), params)
        rows = cur.fetchall() if cur.description else []
        if commit:
            conn.commit()
        rows = [dict(r) for r in rows]
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def init_db():
    pk = "SERIAL PRIMARY KEY" if USE_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"
    query(f"""
        CREATE TABLE IF NOT EXISTS aperturas (
            id {pk},
            nombre TEXT NOT NULL,
            jugadas TEXT NOT NULL,
            nivel TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            imagen_url TEXT,
            video_url TEXT,
            likes INTEGER NOT NULL DEFAULT 0,
            creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""", commit=True)
    query(f"""
        CREATE TABLE IF NOT EXISTS comentarios (
            id {pk},
            apertura_id INTEGER NOT NULL REFERENCES aperturas(id) ON DELETE CASCADE,
            autor TEXT NOT NULL,
            texto TEXT NOT NULL,
            creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""", commit=True)

    total = query("SELECT COUNT(*) AS n FROM aperturas", one=True)["n"]
    if total == 0:
        video = "https://youtu.be/Es_tkcPQJZU"
        semillas = [
            ("Apertura Italiana", "1.e4 e5 2.Cf3 Cc6 3.Ac4", "Principiante",
             "Una de las aperturas más antiguas. El alfil apunta a f7, el punto débil de las negras, "
             "y busca un desarrollo rápido y armónico.", "https://picsum.photos/seed/italiana/800/500", video),
            ("Defensa Siciliana", "1.e4 c5", "Intermedio",
             "La respuesta más popular a 1.e4. Las negras crean un desequilibrio desde la primera jugada "
             "y luchan por el centro desde el flanco.", "https://picsum.photos/seed/siciliana/800/500", video),
            ("Gambito de Dama", "1.d4 d5 2.c4", "Intermedio",
             "Las blancas ofrecen un peón para desviar el peón central negro y dominar el centro.",
             "https://picsum.photos/seed/gambito/800/500", video),
            ("Defensa Francesa", "1.e4 e6", "Principiante",
             "Sólida y estratégica: las negras preparan ...d5 y aceptan un juego algo cerrado a cambio "
             "de una estructura firme.", "https://picsum.photos/seed/francesa/800/500", video),
            ("Defensa India de Rey", "1.d4 Cf6 2.c4 g6", "Avanzado",
             "Las negras ceden el centro al principio para atacarlo después. Muy dinámica y llena de "
             "ataques sobre el rey.", "https://picsum.photos/seed/indiarey/800/500", video),
            ("Apertura Española (Ruy López)", "1.e4 e5 2.Cf3 Cc6 3.Ab5", "Avanzado",
             "Presiona al caballo que defiende e5. Es una de las aperturas más estudiadas de la historia.",
             "https://picsum.photos/seed/espanola/800/500", video),
        ]
        conn = get_conn()
        cur = conn.cursor()
        for s in semillas:
            cur.execute(q("INSERT INTO aperturas (nombre, jugadas, nivel, descripcion, imagen_url, video_url) "
                          "VALUES (%s, %s, %s, %s, %s, %s)"), s)
        conn.commit()
        conn.close()


# ---------------------------------------------------------------- Utilidades
def youtube_id(url):
    """Extrae el ID de un enlace de YouTube (youtu.be, watch?v=, embed/, shorts/)."""
    if not url:
        return None
    m = re.search(r"(?:youtu\.be/|v=|embed/|shorts/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


app.jinja_env.globals["youtube_id"] = youtube_id


def leer_formulario():
    datos = {k: request.form.get(k, "").strip() for k in
             ("nombre", "jugadas", "nivel", "descripcion", "imagen_url", "video_url")}
    errores = []
    if not datos["nombre"]:
        errores.append("El nombre es obligatorio.")
    if not datos["jugadas"]:
        errores.append("Escribe las jugadas iniciales.")
    if datos["nivel"] not in NIVELES:
        errores.append("Elige un nivel válido.")
    if len(datos["descripcion"]) < 10:
        errores.append("La descripción debe tener al menos 10 caracteres.")
    for campo in ("imagen_url", "video_url"):
        if datos[campo] and not datos[campo].startswith(("http://", "https://")):
            errores.append(f"El enlace de {'imagen' if campo == 'imagen_url' else 'video'} debe empezar con https://")
    if datos["video_url"] and not youtube_id(datos["video_url"]):
        errores.append("El video debe ser un enlace de YouTube.")
    return datos, errores


# ---------------------------------------------------------------- Rutas
@app.route("/")
def index():
    buscar = request.args.get("buscar", "").strip()
    nivel = request.args.get("nivel", "")
    sql = "SELECT * FROM aperturas WHERE 1=1"
    params = []
    if buscar:
        sql += " AND (LOWER(nombre) LIKE %s OR LOWER(jugadas) LIKE %s)"
        params += [f"%{buscar.lower()}%"] * 2
    if nivel in NIVELES:
        sql += " AND nivel = %s"
        params.append(nivel)
    sql += " ORDER BY likes DESC, id DESC"
    aperturas = query(sql, params)
    stats = query("SELECT COUNT(*) AS total, COALESCE(SUM(likes),0) AS likes FROM aperturas", one=True)
    ncom = query("SELECT COUNT(*) AS n FROM comentarios", one=True)["n"]
    return render_template("index.html", aperturas=aperturas, buscar=buscar, nivel=nivel,
                           niveles=NIVELES, stats=stats, ncom=ncom)


@app.route("/apertura/<int:id>")
def detalle(id):
    a = query("SELECT * FROM aperturas WHERE id = %s", (id,), one=True)
    if not a:
        abort(404)
    comentarios = query("SELECT * FROM comentarios WHERE apertura_id = %s ORDER BY id DESC", (id,))
    return render_template("detalle.html", a=a, comentarios=comentarios)


@app.route("/nueva", methods=["GET", "POST"])
def nueva():
    if request.method == "POST":
        datos, errores = leer_formulario()
        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("form.html", a=datos, niveles=NIVELES, titulo="Nueva apertura")
        nuevo = query("INSERT INTO aperturas (nombre, jugadas, nivel, descripcion, imagen_url, video_url) "
                      "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                      tuple(datos.values()), one=True, commit=True)
        flash("Apertura agregada correctamente.", "ok")
        return redirect(url_for("detalle", id=nuevo["id"]))
    return render_template("form.html", a={}, niveles=NIVELES, titulo="Nueva apertura")


@app.route("/apertura/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    a = query("SELECT * FROM aperturas WHERE id = %s", (id,), one=True)
    if not a:
        abort(404)
    if request.method == "POST":
        datos, errores = leer_formulario()
        if errores:
            for e in errores:
                flash(e, "error")
            datos["id"] = id
            return render_template("form.html", a=datos, niveles=NIVELES, titulo="Editar apertura")
        query("UPDATE aperturas SET nombre=%s, jugadas=%s, nivel=%s, descripcion=%s, imagen_url=%s, "
              "video_url=%s WHERE id=%s", (*datos.values(), id), commit=True)
        flash("Cambios guardados.", "ok")
        return redirect(url_for("detalle", id=id))
    return render_template("form.html", a=a, niveles=NIVELES, titulo="Editar apertura")


@app.route("/apertura/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    query("DELETE FROM comentarios WHERE apertura_id = %s", (id,), commit=True)
    query("DELETE FROM aperturas WHERE id = %s", (id,), commit=True)
    flash("Apertura eliminada.", "ok")
    return redirect(url_for("index"))


@app.route("/apertura/<int:id>/like", methods=["POST"])
def like(id):
    query("UPDATE aperturas SET likes = likes + 1 WHERE id = %s", (id,), commit=True)
    return redirect(request.referrer or url_for("detalle", id=id))


@app.route("/apertura/<int:id>/comentar", methods=["POST"])
def comentar(id):
    autor = request.form.get("autor", "").strip()[:60]
    texto = request.form.get("texto", "").strip()[:500]
    if autor and texto:
        query("INSERT INTO comentarios (apertura_id, autor, texto) VALUES (%s, %s, %s)",
              (id, autor, texto), commit=True)
        flash("¡Gracias por tu comentario!", "ok")
    else:
        flash("Escribe tu nombre y un comentario.", "error")
    return redirect(url_for("detalle", id=id) + "#comentarios")


@app.errorhandler(404)
def no_encontrado(e):
    return render_template("404.html"), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
