"""One step in Spanish (`names_step`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Un solo paso"
CARD = "Crea un branch nuevo en el commit donde estás y lleva `HEAD` a él, en un solo paso. `git checkout -b <name>` es la forma más vieja."
SCENE = [
    "La vez pasada, empezar un experimento llevó dos comandos: `git branch quiet-engine` y después `git switch quiet-engine`. El comando de hoy es `git switch -c dim-lights`. La `-c` significa crear.",
]

BRIEFING = """
Un tercer experimento: luces tenues, desde `main`, donde estás. `dim.txt` ya está en tu carpeta.
Rama tiene un comando más corto para mostrarte, y después los más viejos que verás en tutoriales
y en el trabajo.

La misión termina cuando `dim-lights` tenga un commit con `dim.txt`, hayas dibujado el árbol,
hayas probado `git checkout` y `git checkout -b`, y hayas listado tus branches.
"""

HINTS = [
    "`git switch -c <name>` es `git branch <name>` y `git switch <name>` juntos.",
    "`git checkout <name>` hace lo mismo que `git switch <name>`; `git checkout -b <name>` hace lo mismo que `git switch -c <name>`.",
    'Cada línea de la misión, en orden:\n\n    $ git switch -c dim-lights\n    $ git add dim.txt\n    $ git commit -m "Try dim lights"\n    $ git log --oneline --graph --all\n    $ git checkout quiet-engine\n    $ git checkout -b night-watch\n    $ git branch -v',
]

DEBRIEF = """
`git switch -c dim-lights` creó el nombre donde estabas y llevó `HEAD` a él; después tu commit hizo
crecer una tercera línea lateral. `git checkout -b` y `git checkout` son las formas más viejas de
`git switch -c` y `git switch`: hacen lo mismo, y el juego acepta cualquiera.

`git checkout` es más viejo y hace muchos trabajos, hasta restaurar archivos, así que Git agregó
`git switch` para un solo trabajo: moverse entre branches. Usa `switch`; lee `checkout` cuando lo
veas.

Comandos para recordar:

    $ git switch -c dim-lights      # un branch nuevo, y ve a él
    $ git checkout -b dim-lights    # lo mismo, forma más vieja
    $ git checkout main             # lo mismo que git switch main
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Escribes `git switch -c dim-lights` estando en `main`. ¿Dónde queda `HEAD` después?",
        options=("En `main`", "En `dim-lights`", "En un commit nuevo"),
        reveal="En `dim-lights`. Git crea el nombre `dim-lights` en el commit donde estás y después lleva `HEAD` a él: los dos comandos de la vez pasada en uno. No se hace ningún commit.",
    ),
    "make": kit.StepText(text="Prueba el comando corto."),
    "commit": kit.StepText(text="Haz commit de `dim.txt`."),
    "graph": kit.StepText(text="Dibuja el árbol."),
    "checkout": kit.StepText(text="Ve a `quiet-engine`, a la manera vieja."),
    "checkout-b": kit.StepText(text="El comando corto, a la manera vieja."),
    "list": kit.StepText(text="Lista tus branches."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_MADE = "Prueba el comando corto: `git switch -c dim-lights`."
MADE = '"A new branch", y estás en él, en un solo paso.'
NOT_ON_DIM = "Haz el commit en `dim-lights`: `git switch dim-lights` te lleva de vuelta."
NOT_COMMITTED = 'Haz commit de `dim.txt` en `dim-lights`: `git add dim.txt` y después `git commit -m "Try dim lights"`.'
COMMITTED = "Una tercera línea lateral desde el mismo commit."
DIM_ON_MAIN = "`main` tiene `dim.txt`: ese commit fue a `main`. Vuelve a empezar la misión y haz el commit en `dim-lights`."
DRAWN = (
    "El dibujo de Git también crece una tercera línea. Dibuja primero el experimento más nuevo, y cada línea lateral se cierra "
    "con su propio `|/`. Compáralo con la cadena por nombre, no por lugar."
)
NOT_DRAWN = "Dibuja el árbol: `git log --oneline --graph --all`."
OLDER_WAY = (
    "Lo mismo que `git switch quiet-engine`. También verás `git checkout` en tutoriales y en el trabajo: es más viejo y hace "
    "muchos trabajos, hasta restaurar archivos, así que Git agregó `git switch` para uno solo, moverse entre branches. Usa `switch`; lee `checkout` cuando lo veas."
)
NOT_OLDER_WAY = "Ve a `quiet-engine`, a la manera vieja: `git checkout quiet-engine`."
NIGHT_MADE = "Lo mismo que `git switch -c night-watch`: un nombre nuevo donde estás, y tú en él."
NOT_NIGHT = "El comando corto, a la manera vieja: `git checkout -b night-watch`, desde `quiet-engine`."
NIGHT_ELSEWHERE = "`night-watch` no está en el commit de `quiet-engine`. Quítalo con `git branch -D night-watch` desde otro branch y vuelve a crearlo desde `quiet-engine`."
LISTED = "Ahora hay seis nombres. `night-watch` y `quiet-engine` nombran el mismo commit."
NOT_LISTED = "Lista tus branches: `git branch -v`."
