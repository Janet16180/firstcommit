"""
Rama's shared texts in Spanish: one constant per text of `firstcommit.reactions`, with the same name.

They follow AUTHORING.md as the English ones do, and docs/i18n-glossary.md, and keep their
commands, file names and code spans exactly (tests/test_translations.py checks it).
"""

NEW_REPOSITORY = "Un repositorio nuevo: Git creó la carpeta oculta `.git`, donde guarda la historia de este proyecto. `ls -a` la muestra."
NOT_A_GIT_COMMAND = "Git no tiene ningún comando con ese nombre. Revisa cómo lo escribiste: `git help -a` lista todos los comandos de Git."
INIT_AGAIN = "Esta carpeta ya era un repositorio. Volver a ejecutar `git init` en ella no tiene riesgo: no sobrescribe nada."
REPOSITORY_GONE = "El repositorio ya no está, y su historia tampoco: Git la guardaba entera en la carpeta `.git`."
NO_REPOSITORY = "Git no encontró ningún repositorio aquí. Este comando solo funciona dentro de un repositorio, y `git init` convierte esta carpeta en uno."
STATUS = "`git status` lista lo que está en el staging area para tu próximo commit, lo que cambió después en la carpeta de trabajo y los archivos que Git aún no sigue."
UNSTAGED = "Fuera del staging area: tu próximo commit no se llevará ese cambio."
RESTORED = "`git restore` reemplazó el archivo en la carpeta de trabajo: los cambios que tenía ahí y que no habías agregado al staging area se perdieron."
STAGED = "En el staging area: tu próximo commit se llevará el archivo tal como está ahora. Si lo vuelves a cambiar, tendrás que agregarlo otra vez."
NOTHING_NEW = "Nada nuevo que agregar: el staging area ya coincidía."
ADD_WHAT = "`git add` necesita saber qué agregar al staging area: el nombre de un archivo, o `.` para todo lo de esta carpeta y las carpetas que contiene."
NOT_STAGED = "No se agregó nada al staging area. Lee el mensaje de Git: lo habitual es un nombre que no encuentra. `ls` lista la carpeta, y la tecla Tab completa los nombres."
COMMITTED = "Commit hecho: una cápsula nueva sellada en tu repositorio (la bóveda), con su propio hash y tu mensaje. `git log --oneline` la lista."
NO_MESSAGE = (
    "No se hizo ningún commit: todo commit necesita un mensaje, y en el juego no se abre ningún editor para escribirlo. "
    'Dalo en la misma línea: `git commit -m "Add the map"`.'
)
NOT_COMMITTED = "No se hizo ningún commit. Lee el mensaje de Git; lo habitual es que no haya nada nuevo en el staging area: primero haz `git add` de tus cambios, o `git commit -am` agrega los archivos que Git ya sigue."
NO_REMOTE = "Tu repositorio todavía no conoce ningún remoto, así que el push no tenía adónde ir. Primero nombra uno: `git remote add origin` y su dirección."
FETCHED = (
    "Fetch hecho: los commits nuevos del remoto (la nave nodriza) ya están en tu repositorio, en branches como `origin/main`. "
    "Tus propios branches y tus archivos no se movieron."
)
FETCHED_NOTHING = "Nada nuevo en el remoto (la nave nodriza): tu repositorio ya tenía todos sus commits."
PULLED_FAST_FORWARD = (
    "Pull hecho con un fast-forward: no tenías commits nuevos propios, así que Git solo movió tu branch hasta el commit más reciente del remoto (la nave nodriza). "
    "No hizo falta un commit de merge."
)
PULLED_MERGE = "Pull hecho: tú y el remoto (la nave nodriza) tenían commits nuevos, así que Git los unió en un commit de merge con dos padres."
PULLED_NOTHING = "Ya estaba al día: el remoto (la nave nodriza) no tenía nada que le faltara a tu branch."
LOG_FILE = "Solo los commits que cambiaron ese archivo, del más reciente al más antiguo: la historia de un archivo, dentro de toda la historia."
LOG = "Tu historia, del commit más reciente al más antiguo. Cada commit guarda su autor, su fecha y su mensaje, y Git lo nombra por su hash."
HIDDEN_GIT = "¿Ves `.git`? Esa carpeta oculta es el repositorio: Git guarda en ella toda la historia. Un `ls` a secas oculta los nombres que empiezan con punto."
LS_IN_REPOSITORY = "`ls` lista la carpeta de trabajo. Para ver cuáles de estos archivos cambiaron, y cuáles aún no sigue Git, pregúntale a `git status`."
LS_NO_REPOSITORY = "Archivos normales en una carpeta normal: Git todavía no guarda ninguna historia de ellos."
DID_YOU_MEAN_GIT = "¿Querías escribir `git`? Le pasa a toda la tripulación."
UNKNOWN_COMMAND = "La terminal no conoce ningún comando con ese nombre. Revisa cómo lo escribiste: la tecla Tab también completa los nombres de los comandos."
NEW_FILE = "Un archivo nuevo en la carpeta de trabajo. Git aún no lo sigue: `git status` lo lista como sin seguimiento hasta que hagas `git add`."
CHANGED_FILE = "Cambiaste un archivo en la carpeta de trabajo. Lo que está en el staging area se queda como estaba hasta que vuelvas a hacer `git add` del archivo."
MERGETOOL_ANSWERED = (
    "La herramienta de merge escribió tu respuesta, y Git agregó el archivo al staging area (el muelle de carga) por su cuenta: esta vez no hace falta `git add`. "
    "`git status` lo muestra."
)
MERGETOOL_STOPPED = "La herramienta de merge se detuvo antes de una respuesta, así que Git dejó el archivo como estaba, con sus marcadores. No se perdió nada: ejecuta `git mergetool` otra vez cuando quieras."
MERGETOOL_NOTHING = "Ningún archivo está en conflicto, así que Git no abrió ninguna herramienta de merge: solo abre una para los archivos que un merge dejó en conflicto."
MERGETOOL_OTHER = "`--tool` elige otro programa solo para esta vez; vimdiff, por ejemplo, se abre dentro de tu terminal. En el juego, `git mergetool` a secas abre el panel de merge del juego."
