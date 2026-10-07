"""
Rama's shared texts in Spanish: one constant per text of `firstcommit.reactions`, with the same name.

They follow AUTHORING.md as the English ones do, and keep their commands, file names and code
spans exactly (tests/test_translations.py checks it).
"""

NEW_REPOSITORY = "Un repositorio nuevo: Git ha creado la carpeta oculta `.git`, donde guarda la historia de este proyecto. `ls -a` la muestra."
NOT_A_GIT_COMMAND = "Git no tiene ningún comando con ese nombre. Revisa cómo lo has escrito: `git help -a` lista todos los comandos de Git."
INIT_AGAIN = "Esta carpeta ya era un repositorio. Volver a ejecutar `git init` en ella no tiene riesgo: no sobrescribe nada."
REPOSITORY_GONE = "El repositorio ya no está, y su historia tampoco: Git la guardaba entera en la carpeta `.git`."
NO_REPOSITORY = "Git no encuentra ningún repositorio aquí. Este comando solo funciona dentro de un repositorio, y `git init` convierte esta carpeta en uno."
STATUS = "`git status` lista lo que está preparado para tu próximo commit, lo que ha cambiado después en la carpeta de trabajo y los archivos que Git aún no sigue."
UNSTAGED = "Fuera del área de preparación: tu próximo commit no se llevará ese cambio."
RESTORED = "`git restore` ha reemplazado el archivo en la carpeta de trabajo: los cambios que tenía ahí y que no habías preparado se han perdido."
STAGED = "Preparado: tu próximo commit se llevará el archivo tal como está ahora. Si lo vuelves a cambiar, tendrás que volver a prepararlo."
NOTHING_NEW = "Nada nuevo que preparar: el área de preparación ya coincidía."
ADD_WHAT = "`git add` necesita saber qué preparar: el nombre de un archivo, o `.` para todo lo de esta carpeta y las carpetas que contiene."
NOT_STAGED = "No se ha preparado nada. Lee el mensaje de Git: lo habitual es un nombre que no encuentra. `ls` lista la carpeta, y el tabulador completa los nombres."
COMMITTED = "Commit hecho: una caja cerrada nueva en tu repositorio, con su propio hash y tu mensaje. `git log --oneline` la lista."
NO_MESSAGE = (
    "No se ha hecho ningún commit: todo commit necesita un mensaje, y en el juego no se abre ningún editor para escribirlo. "
    'Dalo en la misma línea: `git commit -m "Add the map"`.'
)
NOT_COMMITTED = "No se ha hecho ningún commit. Lee el mensaje de Git: lo habitual es que no haya nada nuevo en el área de preparación, o que aún no tengas nombre y correo configurados."
LOG = "Tu historia, del commit más reciente al más antiguo. Cada commit guarda su autor, su fecha y su mensaje, y Git lo nombra por su hash."
HIDDEN_GIT = "¿Ves `.git`? Esa carpeta oculta es el repositorio: Git guarda en ella toda la historia. Un `ls` a secas oculta los nombres que empiezan por punto."
LS_IN_REPOSITORY = "`ls` lista la carpeta de trabajo. Para ver cuáles de estos archivos han cambiado, y cuáles aún no sigue Git, pregunta a `git status`."
LS_NO_REPOSITORY = "Archivos normales en una carpeta normal: Git todavía no guarda ninguna historia de ellos."
DID_YOU_MEAN_GIT = "¿Querías escribir `git`? Le pasa a toda la tripulación."
UNKNOWN_COMMAND = "La terminal no conoce ningún comando con ese nombre. Revisa cómo lo has escrito: el tabulador también completa los nombres de los comandos."
NEW_FILE = "Un archivo nuevo en la carpeta de trabajo. Git aún no lo sigue: `git status` lo lista como sin seguimiento hasta que hagas `git add`."
CHANGED_FILE = "Has cambiado un archivo en la carpeta de trabajo. Lo preparado se queda como estaba hasta que vuelvas a hacer `git add` del archivo."
