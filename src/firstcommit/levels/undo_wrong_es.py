"""Wrong course in Spanish (`undo_wrong`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Rumbo equivocado"
CARD = "Mueve el branch donde estás a otro commit, y hace que tu carpeta coincida con él. Los commits que deja siguen en Git; un branch sobre ellos hace que sea fácil encontrarlos."
SCENE = [
    "Dos commits de un relevamiento cayeron en `main` por error. El pin del remoto (la nave nodriza) está dos commits más abajo: no los vio. Tu carpeta tiene `survey.txt`, de esos commits.",
]

BRIEFING = """
Hiciste por error dos commits de un relevamiento en `main`: les corresponde un branch propio, y la
nave nodriza todavía no los vio. Guárdalos en un branch `rescue` y lleva `main` de vuelta a donde
está el `main` de la nave nodriza.

La misión termina cuando `rescue` tenga tus dos commits, `main` haya vuelto a `origin/main` con tu
carpeta igual a él, y hayas revisado la historia.
"""

HINTS = [
    "`git branch rescue` pone un nombre nuevo en el commit donde estás, así los dos commits conservan un nombre.",
    "`git reset --hard origin/main` mueve el branch donde estás, `main`, a donde está `origin/main`, y hace que tus archivos coincidan.",
    "Cada línea de la misión, en orden:\n\n    $ git branch rescue\n    $ git reset --hard origin/main\n    $ git log --oneline",
]

DEBRIEF = """
`git reset --hard origin/main` movió el branch donde estabas, `main`, hacia atrás en la cadena, e
hizo que tu carpeta coincidiera con ese commit. No borró ningún commit: tus dos commits siguen ahí,
con `rescue`.

Sin `--hard`, reset mueve el branch y deja tus archivos como están. Usa reset solo con commits que
nadie más tiene: en un branch que otros ya trajeron con pull, `git revert` es la forma segura de
deshacer.

Comandos para recordar:

    $ git branch rescue              # primero, un nombre sobre los commits
    $ git reset --hard origin/main   # después, mueve main hacia atrás
"""

STEPS = {
    "rescue": kit.StepText(text="Guarda tus commits en un branch."),
    "guess": kit.StepText(
        text="Primero, predice.",
        question="Después del reset, ¿cuántos commits mostrará `git log --oneline`?",
        options=("1", "3"),
        reveal="1. `git log` empieza en `HEAD` y baja por los padres. `HEAD` va sobre `main`, que estará en *Start the project*, el commit más viejo. Los dos commits del relevamiento están por encima, donde solo lleva `rescue`.",
    ),
    "reset": kit.StepText(text="Mueve `main` hacia atrás."),
    "log": kit.StepText(text="Revisa."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_LABELLED = "Primero guarda tus commits en un branch: `git branch rescue`."
LABELLED = (
    "`rescue` es un segundo nombre en el mismo commit. Nada más cambió: ningún commit nuevo, ningún archivo. `HEAD` sigue sobre `main`. "
    "Ahora, `git reset --hard origin/main` mueve el branch donde estás, `main`, al commit donde está tu marcador `origin/main`, "
    "*Start the project*. `--hard` además hace que tu carpeta coincida con ese commit; sin él, el branch se mueve y tus archivos quedan como están."
)
GHOSTS = (
    "Ningún branch lleva ahora a tus dos commits, pero Git todavía los tiene. La próxima misión muestra cómo encontrarlos; por "
    "ahora, vuelve a empezar con Reiniciar."
)
NOT_RESET = "`main` todavía tiene los dos commits. Muévelo hacia atrás: `git reset --hard origin/main`."
DIRTY = "`main` volvió, pero tu carpeta no coincide con él. `git reset --hard origin/main` la hace coincidir."
RESET = (
    '`main` bajó dos commits, y `HEAD` fue con él: "HEAD is now at" nombra dónde estás. Los commits no se movieron: '
    "`rescue` todavía los tiene. `survey.txt` salió de tu carpeta."
)
LOGGED = (
    "Un commit, como predijiste. `git log` baja desde `HEAD`, y nada debajo de *Start the project* lleva a los commits del "
    "relevamiento. Siguen en Git: `rescue` lleva a ellos. ¿Y si no hubieras creado el branch? Ningún branch llevaría a los dos "
    "commits. Git guarda los commits a los que no lleva ningún branch unos 30 días, después puede borrarlos, y `git log` no los mostraría."
)
NOT_LOGGED = "Revisa: `git log --oneline`."
SHARED = "El `main` de la nave nodriza ya tiene tus dos commits del relevamiento: otros pueden traerlos con pull. Vuelve a empezar la misión."
MOVED_BACK = "`main` volvió atrás. Los commits que dejó siguen en Git."
