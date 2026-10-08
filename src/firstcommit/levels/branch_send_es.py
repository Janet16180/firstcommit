"""Send a course up in Spanish (`branch_send`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Sube un rumbo"
CARD = "Envía ese branch al remoto, por su nombre, desde el branch donde estés. Un `git push` simple envía solo el branch donde estás, a su upstream."
SCENE = [
    "Tu exploración está en un segundo rumbo, `scout`, de dos cápsulas.",
    "La nave nodriza recibe solo lo que le envías, un branch a la vez.",
]

BRIEFING = """
Tu exploración está en el branch `scout`, con dos commits. `main` está al día con la nave nodriza.
El equipo quiere revisar la exploración, así que debe llegar a la nave nodriza, y su `main` no
debe cambiar.

La misión termina cuando hayas hecho push desde `main`, la nave nodriza tenga `scout` en el commit
de tu `scout` con su `main` sin cambios, y hayas listado los branches del remoto con
`git branch -r`.
"""

HINTS = [
    "En `main`, `git push` envía solo `main`. Mira qué tiene la nave nodriza después.",
    "Nombra el branch para enviarlo: `git push -u origin scout` funciona desde cualquier branch.",
    "`git branch -r` lista lo que tu repositorio sabe de los branches del remoto, como `origin/main`.",
    "Cada línea de la misión, en orden:\n\n    $ git push\n    $ git push -u origin scout\n    $ git branch -r",
]

DEBRIEF = """
Un `git push` simple en `main` envió `main`, que no tenía nada nuevo, y dejó `scout` aquí. Un push
envía un solo branch, salvo que pidas más. `git push -u origin scout` nombró el branch: ahora la
nave nodriza tiene `scout` para que el equipo lo revise, y su `main` no se movió. `-u` hizo de
`origin/scout` el upstream de tu `scout`, así que la próxima vez un `git push` simple en `scout`
lo envía.

`git branch -r` lista lo que tu repositorio registró de los branches del remoto: `origin/main`, y
ahora `origin/scout`.

En el trabajo, haces push del branch de tu tarea por su nombre y pides una revisión; `main` cambia
solo cuando se hace merge de esa revisión.

Comandos para recordar:

    $ git push -u origin scout   # envía un branch nuevo, por su nombre, y lo sigue
    $ git branch -r              # los branches del remoto, según las últimas noticias
"""

STEPS = {
    "push": kit.StepText(text="Haz push desde `main`, como en el capítulo anterior."),
    "send": kit.StepText(text="Envía `scout` a la nave nodriza, por su nombre."),
    "list": kit.StepText(text="Lista los branches del remoto."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_PUSHED = "Primero haz push desde `main`: `git push`."
PUSHED_MAIN = "Un `git push` simple envió solo `main`. La nave nodriza todavía no tiene `scout`."
NOT_SENT = "La nave nodriza todavía no tiene `scout`. Envíalo por su nombre: `git push -u origin scout`."
BEHIND = "El `scout` de la nave nodriza no está en el commit de tu `scout`. Envíalo otra vez: `git push origin scout`."
MAIN_MOVED = "El `main` de la nave nodriza cambió: la exploración debe llegar a él solo con una revisión. Vuelve a empezar la misión."
SENT = "Ahora la nave nodriza tiene `scout`, con los dos commits de la exploración; su `main` no cambió."
LISTED = "`origin/scout` está junto a `origin/main`: lo que tu repositorio registró de los branches de la nave nodriza."
NOT_LISTED = "Lista los branches del remoto: `git branch -r`."
NO_UPSTREAM = (
    "`scout` todavía no tiene upstream, así que un `git push` simple no sabe adónde enviarlo. Nombra el remoto y el "
    "branch una vez: `git push -u origin scout`."
)
