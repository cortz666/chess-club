# Chess Atelier · Club de Aperturas

Aplicación web dinámica hecha con **Flask (Python)** y **PostgreSQL**, publicada en **Render**.

## Cumplimiento de la actividad
| Requisito | Cómo se cumple |
|---|---|
| Base de datos | PostgreSQL de Render: tablas `aperturas` y `comentarios`. CRUD completo (agregar, ver, editar, eliminar), búsqueda, filtro por nivel, "me gusta" y comentarios. |
| Interfaz responsiva | CSS Grid/Flexbox, `clamp()`, media queries a 900 px y 680 px, menú hamburguesa en celular, videos 16:9 adaptables. |
| Medios digitales de otras nubes | Videos de **YouTube** incrustados, imágenes desde **Lorem Picsum** (o Cloudinary/Imgur por enlace), tipografías de **Google Fonts**, enlace a **Lichess**. |

## Probar en tu computadora (opcional)
```bash
pip install -r requirements.txt
python app.py
```
Abre http://127.0.0.1:5000 (en local usa SQLite, archivo `club.db`).

## Publicar en Render (paso a paso)
1. Crea una cuenta en https://github.com y un repositorio nuevo, por ejemplo `chess-atelier-club`.
2. Sube todos los archivos de esta carpeta al repositorio (botón **Add file → Upload files**, arrastra todo y da **Commit changes**). Las carpetas `templates` y `static` deben quedar tal cual.
3. Entra a https://render.com e inicia sesión con tu cuenta de GitHub.
4. Da clic en **New + → Blueprint**, elige tu repositorio y confirma. Render lee el archivo `render.yaml` y crea automáticamente:
   - el servicio web `chess-atelier-club` (plan Free)
   - la base de datos PostgreSQL `chess-club-db` (plan Free) y la conecta con `DATABASE_URL`.
5. Espera a que el deploy diga **Live** (3–5 min). Tu URL será algo como `https://chess-atelier-club.onrender.com`.
6. Al abrirla por primera vez, la app crea las tablas y carga 6 aperturas de ejemplo.

> Nota: en el plan gratuito el servicio "se duerme" tras 15 min sin visitas; la primera carga después tarda ~50 s. La base de datos gratuita de Render dura 30 días, suficiente para la evaluación.

### Alternativa: Railway
Si ya usaste Render en otra actividad: en https://railway.app → **New Project → Deploy from GitHub repo**, luego **+ New → Database → PostgreSQL** y en las variables del servicio web agrega `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`. El archivo `Procfile` ya indica cómo arrancar la app. En **Settings → Networking → Generate Domain** obtienes la URL.

## Cambiar las imágenes y videos
Desde la propia app (botón **Editar**) pega cualquier enlace de imagen (Cloudinary, Imgur, Wikimedia…) y cualquier enlace de YouTube.
