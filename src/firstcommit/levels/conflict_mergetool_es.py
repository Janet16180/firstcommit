"""Merge tools in Spanish (`conflict_mergetool`), written with docs/i18n-glossary.md."""

from firstcommit import kit

AGAIN = "Para responder otra vez: `git merge --abort`, luego `git merge --no-edit scout` y `git mergetool`."

TITLE = "Herramientas de merge"
CARD = "Abre la herramienta de merge que nombra `merge.tool` en cada archivo en conflicto, uno tras otro. Cuando la herramienta informa que terminó bien, Git agrega el archivo al staging area. En el juego abre el panel de merge del propio juego."
SCENE = [
    "Las dos tripulaciones cambiaron el plan de lanzamiento, y se partió en dos lugares.",
    "Ya conoces el camino de la terminal. Hoy Git te abre una herramienta: un clic por conflicto.",
]

BRIEFING = """
Moviste el lanzamiento a las 07:00 y cargaste oxígeno, en `main`. Alex, en `scout`, lo movió a las
05:30 y cargó una antena de repuesto: la ventana de lanzamiento cierra temprano. Trae `scout` a
`main` y responde los dos conflictos con una herramienta de merge: la hora de Alex, y las dos
líneas de carga.

La misión termina cuando el último commit de `main` tenga el trabajo de `scout`, lance a las 05:30
y cargue tanto el oxígeno como la antena de repuesto, sin marcadores de conflicto.
"""

HINTS = [
    "`git merge --no-edit scout` se detiene con dos conflictos en `launch.txt`. Luego `git mergetool` abre el panel de merge del juego.",
    "En el panel, quédate con la hora de lanzamiento de Alex y con las dos líneas de carga (Las dos), y luego presiona Escribir. La herramienta agrega `launch.txt` por su cuenta, así que las líneas siguientes son `git status` y `git commit --no-edit`.",
    "Cada línea de la misión, en orden. En el panel, elige la de Alex, luego Las dos, y luego presiona Escribir:\n\n    $ git merge --no-edit scout\n    $ git mergetool\n    $ git status\n    $ git commit --no-edit",
]

DEBRIEF = """
`git mergetool` abrió una herramienta de merge en el archivo en conflicto: aquí, el panel del
juego. Respondiste cada conflicto por separado, Escribir guardó el archivo, y cuando la
herramienta terminó, Git agregó `launch.txt` al staging area (el muelle de carga) por su cuenta.
`git commit --no-edit` terminó el merge, como en la 7-3. `git restore --theirs` no habría
podido: se queda con un lado para el archivo entero.

Las herramientas reales son distintas. El panel es una herramienta de entrenamiento: un clic por
conflicto, hecha para aprender. En el trabajo, la gente responde los conflictos en la vista de
merge de su editor o en una herramienta de merge. En VS Code, su editor de merge se abre por lo
general desde el archivo en conflicto o desde la vista de Source Control; también se puede
configurar como la herramienta de merge de git. Una herramienta como Meld es lo que abre
`git mergetool` una vez que configuras la tuya: `git config merge.tool meld`. Las herramientas
reales muestran más del archivo y te dejan escribir una respuesta línea por línea, para cuando
ningún lado solo es el correcto.

El juego también esconde dos cosas que git hace por su cuenta. Guarda el archivo como estaba, con
sus marcadores, como `launch.txt.orig` después de cada respuesta, hasta que lo borres. Y cuando no
hay ninguna herramienta configurada, elige una que encuentre y pregunta "Hit return to start merge
resolution tool" antes de abrirla.

El camino de la terminal de la 7-3 funciona en todas partes, con herramienta o sin ella, y
`git merge --abort` también.

Comandos para recordar:

    $ git mergetool   # abre la herramienta de merge en cada archivo en conflicto; agrega cada respuesta
"""

STEPS = {
    "merge": kit.StepText(text="Trae `scout` a `main`."),
    "answer": kit.StepText(text="Abre la herramienta de merge y responde cada conflicto. En el panel, quédate con la hora de lanzamiento de Alex y con las dos líneas de carga, y luego presiona Escribir."),
    "status": kit.StepText(text="Mira lo que hizo la herramienta."),
    "commit": kit.StepText(text="Termina el merge."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_STARTED = "Trae `scout`: `git merge --no-edit scout`."
CONFLICT = "El merge se detuvo: `launch.txt` tiene dos conflictos."
NOT_ANSWERED = "Responde los dos conflictos: `git mergetool` abre el panel de merge. Quédate con la hora de lanzamiento de Alex y con las dos líneas de carga."
MARKERS = f"`launch.txt` está en el staging area todavía con marcadores de conflicto. {AGAIN}"
LATE = f"`launch.txt` lanza a las 07:00, después de que cierra la ventana. {AGAIN}"
ONE_CARGO = f"Solo una línea de carga llegó a `launch.txt`; el viaje necesita las dos. {AGAIN}"
OTHER = f"`launch.txt` debería lanzar a las 05:30 y cargar tanto el oxígeno como la antena de repuesto. {AGAIN}"
ANSWERED = "`launch.txt` lanza a las 05:30 y carga las dos cosas, sin marcadores."
NOT_LOOKED = "Mira lo que hizo la herramienta: `git status`."
LOOKED = "`launch.txt` está en el staging area (el muelle de carga): la herramienta lo agregó por ti."
NOT_COMMITTED = "Termina el merge: `git commit --no-edit`."
WRONG_COMMITTED = "El último commit de `main` no lanza a las 05:30 con las dos líneas de carga. Sal de la misión y vuelve a empezarla, y elige la hora de Alex y Las dos."
DONE = "El último commit de `main` tiene el trabajo de `scout`, lanza a las 05:30 y carga las dos cosas."
ANSWER_FIRST = "Git no puede hacer commit mientras un archivo está en conflicto. Respóndelo primero: `git mergetool`."
ONE_SIDE = f"Eso se queda con un lado del archivo entero, así que se fue una línea del otro lado. Aquí cada conflicto necesita su propia respuesta. {AGAIN}"
