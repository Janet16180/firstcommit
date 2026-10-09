"""The move log in Spanish (`undo_movelog`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "El log de movimientos"
CARD = "El log de movimientos: cada lugar donde estuvo `HEAD`, del más nuevo al más viejo. `HEAD@{1}` nombra dónde estaba `HEAD` hace un movimiento."
SCENE = [
    "Al día siguiente, el mismo error: dos commits del relevamiento en `main`. Esta vez llevaste `main` hacia atrás y olvidaste nombrarlos. La cadena muestra solo *Start the project*: ningún branch lleva a los commits del relevamiento, y todavía no los buscaste.",
]

BRIEFING = """
Al día siguiente, el mismo error: dos commits del relevamiento en `main`. Esta vez llevaste `main`
hacia atrás con `git reset --hard origin/main` y olvidaste nombrarlos. Encuentra los dos commits y
ponles un branch `survey`.

La misión termina cuando `survey` tenga los dos commits del relevamiento, estés en él y hayas
vuelto a leer el log de movimientos.
"""

HINTS = [
    "`git log` solo camina hacia atrás desde donde estás. `git reflog` lista cada lugar donde estuvo `HEAD`, incluso commits a los que no lleva ningún branch.",
    "Busca la línea `commit: Survey day 2` en el log de movimientos; el `HEAD@{n}` después de su hash nombra ese commit. `git branch survey` seguido de ese nombre le pone un nombre.",
    "Cada línea de la misión, en orden:\n\n    $ git log --oneline\n    $ git reflog\n    $ git branch survey HEAD@{1}\n    $ git switch survey\n    $ git reflog",
]

DEBRIEF = """
`git log` solo camina hacia atrás desde `HEAD` por los padres, así que no podía ver el relevamiento.
`git reflog` lista cada movimiento de `HEAD`, del más nuevo al más viejo, y `HEAD@{1}` nombró el
commit de hace un movimiento. `git branch survey HEAD@{1}` le puso un nombre, y los dos commits
volvieron.

El hash al principio de cada línea también sirve, y a diferencia de `HEAD@{n}` nunca cambia. El
log de movimientos vive solo en tu repositorio, y Git guarda unos 30 días los commits a los que no
lleva ningún branch. Un branch los guarda para siempre.

Comandos para recordar:

    $ git reflog                    # cada lugar donde estuvo HEAD
    $ git branch survey HEAD@{1}    # un nombre en un commit del log de movimientos
"""

STEPS = {
    "log": kit.StepText(text="Búscalos en la historia."),
    "reflog": kit.StepText(text="Lee el log de movimientos."),
    "name": kit.StepText(text="Pon un branch `survey` en *Survey day 2*."),
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Ahora vas al branch con `git switch survey`. Después, ¿qué número tendrá la línea `commit: Survey day 2`?",
        options=("Sigue siendo `HEAD@{1}`", "`HEAD@{2}`", "`HEAD@{0}`"),
        reveal="`HEAD@{2}`. Ir a un branch es un movimiento, así que se vuelve la línea más nueva, `HEAD@{0}`, y cada línea más vieja cuenta uno más hacia atrás.",
    ),
    "switch": kit.StepText(text="Ve allí."),
    "reflog-again": kit.StepText(text="Vuelve a leer el log de movimientos."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOGGED = "`git log` empieza en `HEAD` y camina hacia atrás por los padres. Los commits del relevamiento vinieron después de *Start the project*, y ningún branch lleva a ellos, así que `git log` no puede listarlos."
NOT_LOGGED = "Búscalos en la historia: `git log --oneline`."
READ = (
    "`git log` es la historia de tus commits. `git reflog` es la historia de tus movimientos: cada lugar donde estuvo `HEAD`, el "
    "más nuevo arriba, como la lista de páginas visitadas de tu navegador, que incluye hasta las que cerraste. Vive solo en tu computadora. "
    "Léelo de abajo hacia arriba: el clone, tus dos commits del relevamiento y después el reset hasta donde estás ahora. El "
    "`HEAD@{n}` de cada línea nombra ese lugar: `HEAD@{0}` es donde estás ahora, `HEAD@{1}` donde estabas hace un movimiento. "
    "`HEAD~1` camina hacia atrás por los padres; `HEAD@{1}` camina hacia atrás por tus propios movimientos."
)
NOT_READ = "Lee el log de movimientos: `git reflog`."
NOT_NAMED = "Pon un branch `survey` en *Survey day 2*: `git branch survey` y el `HEAD@{n}` de su línea."
WRONG_LINE = "`survey` está en *Start the project*, donde estás ahora. *Survey day 2* está un movimiento atrás: `HEAD@{1}`. Quita el nombre con `git branch -d survey` y vuelve a intentarlo."
NAMED = "Un nombre en *Survey day 2*, y los dos commits del relevamiento vuelven a estar sólidos: *Survey day 1* es su padre. Nunca se habían ido."
NOT_ON = "Ve allí: `git switch survey`."
ON = "Estás en `survey`, y `survey.txt` volvió a tu carpeta. Vuelve a leer el log de movimientos."
READ_AGAIN = (
    "Una línea nueva arriba, y cada número creció en uno: *Survey day 2* era `HEAD@{1}`, ahora es `HEAD@{2}`. Los números cuentan "
    "hacia atrás desde ahora, así que lee el log de movimientos justo antes de usarlo, o usa el hash al principio de la línea: "
    "nunca cambia. La línea nueva dice `checkout`: es el nombre más viejo de `git switch`."
)
NOT_READ_AGAIN = "Vuelve a leer el log de movimientos: `git reflog`."
ERASED = "Los commits del relevamiento se perdieron para siempre. Vuelve a empezar la misión."
WIPE = "Eso limpia los commits a los que no lleva ningún branch: se pueden borrar para siempre cuando el log de movimientos los olvida. Primero ponles un nombre."
WRONG_LINE_SAID = "`survey` está en *Start the project*, donde estás ahora. *Survey day 2* está un movimiento atrás: `HEAD@{1}`."
