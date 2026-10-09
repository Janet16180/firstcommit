"""Two experiments in Spanish (`names_experiments`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Dos experimentos"
CARD = "Lleva `HEAD` a otro branch, y tu carpeta cambia para mostrar el commit de ese branch."
SCENE = [
    "El experimento de ayer es la línea lateral de la derecha: `bright-lights` y su commit, *Try bright lights*, unido a *Fix the route*. Volviste a `main`. La fila bajo la cadena es tu carpeta de trabajo: `engine.txt` espera ahí, todavía fuera de Git.",
]

BRIEFING = """
Ayer empezaste un experimento, `bright-lights`, en su propio branch, y volviste a `main`. Hoy el
capitán quiere probar un segundo, `quiet-engine`, al lado; `engine.txt` ya está escrito y espera
en tu carpeta. `main` queda como está.

La misión termina cuando `quiet-engine` tenga un commit con `engine.txt`, estés en
`bright-lights` y hayas dibujado el árbol.
"""

HINTS = [
    "`git branch <name>` crea un nombre donde estás; `git switch <name>` lleva `HEAD` a él.",
    "`git add engine.txt` y después `git commit -m`, estando en `quiet-engine`.",
    'Cada línea de la misión, en orden:\n\n    $ git branch quiet-engine\n    $ git switch quiet-engine\n    $ git add engine.txt\n    $ git commit -m "Try a quiet engine"\n    $ git switch bright-lights\n    $ git log --oneline --graph --all',
]

DEBRIEF = """
Dos branches creados desde el mismo commit hicieron que la cadena se bifurcara. `git switch` llevó
`HEAD` de un experimento al otro, y cada vez tu carpeta cambió para mostrar el commit de ese
branch. Un commit mueve solo el nombre donde está `HEAD`, así que `main` nunca se movió.

`git log --oneline --graph --all` dibuja el árbol completo en la terminal, con todos los branches.

Comandos para recordar:

    $ git switch bright-lights            # lleva HEAD a otro branch
    $ git log --oneline --graph --all     # el árbol completo, dibujado
"""

STEPS = {
    "branch": kit.StepText(text="Pon un nombre en el commit de `main`."),
    "switch": kit.StepText(text="Ve allí."),
    "commit": kit.StepText(text="Haz commit de `engine.txt` allí."),
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Cambias a `bright-lights`. ¿Sigue `engine.txt` en tu carpeta?",
        options=("Sí", "No"),
        reveal="No. La carpeta muestra el commit de `bright-lights`: vuelve `lights.txt` y se va `engine.txt`. Los dos archivos están a salvo en sus commits.",
    ),
    "bright": kit.StepText(text="Cambia al otro experimento."),
    "graph": kit.StepText(text="Dibuja el árbol."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_NAMED = "Pon un nombre en el commit de `main`: `git branch quiet-engine`."
NAMED = "Un segundo nombre en el commit de `main`. `HEAD` sigue en `main`."
NOT_ON_QUIET = "Ve allí: `git switch quiet-engine`."
ON_QUIET = "`HEAD` pasó a `quiet-engine`. Tu carpeta no cambió: los dos nombres están en el mismo commit, y `engine.txt` todavía no está en Git, así que un switch no lo toca."
NOT_COMMITTED = 'Haz commit de `engine.txt` en `quiet-engine`: `git add engine.txt` y después `git commit -m "Try a quiet engine"`.'
COMMITTED = "`quiet-engine` subió al commit nuevo, y `main` se quedó. Dos líneas laterales desde el mismo commit: la cadena se bifurca, como un árbol. Cada experimento tiene su propio nombre y su propio commit."
MAIN_MOVED = "`main` se movió, y el capitán quería dejarlo como estaba. Vuelve a empezar la misión para intentarlo otra vez."
NOT_ON_BRIGHT = "Cambia al otro experimento: `git switch bright-lights`."
ON_BRIGHT = "`HEAD` saltó por el árbol al otro experimento, y la carpeta lo siguió: entra `lights.txt`, sale `engine.txt`."
DRAWN = (
    "El mismo árbol, dibujado por git en la terminal. Cada `*` es un commit, y `|` y `/` son las líneas entre ellos. "
    "`--all` muestra todos los branches, no solo la línea donde estás. Tus dos experimentos están marcados en los dos dibujos."
)
NOT_DRAWN = "Dibuja el árbol: `git log --oneline --graph --all`."
OLDER_FORM_WORKS = "Eso también funciona: `git checkout <name>` es la forma más vieja de `git switch <name>`."
