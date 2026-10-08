"""Recall the capsule in Spanish (`undo_recall`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Retira la cápsula"
CARD = "Crea un commit nuevo que deshace uno anterior. El commit anterior se queda en la historia, así que es seguro en un branch que otros ya trajeron con pull."
SCENE = [
    "Ayer hiciste push del commit de las luces estroboscópicas y después de la ruta nocturna. Los pines muestran que el remoto (la nave nodriza) y Alex tienen los dos.",
]

BRIEFING = """
Ayer hiciste push de un commit que puso las luces de la estación en modo estroboscópico, y después
de uno bueno con la ruta nocturna. Alex trajo los dos con pull, y las luces le dan dolor de cabeza
a todos. Deshaz las luces estroboscópicas para toda la tripulación, y conserva la ruta nocturna.

La misión termina cuando hayas leído la historia con `git log`, tu `main` tenga un commit que
deshaga las luces estroboscópicas, y el `main` de la nave nodriza también lo tenga.
"""

HINTS = [
    "`git log --oneline` lista los commits, del más reciente al más antiguo: el de las luces es el segundo desde arriba, `HEAD~1`.",
    "`git revert HEAD~1` crea un commit nuevo que lo deshace; después, `git push` envía ese commit.",
    "Cada línea de la misión, en orden:\n\n    $ git log --oneline\n    $ git revert HEAD~1\n    $ git push",
]

DEBRIEF = """
`git revert HEAD~1` no quitó el commit de las luces: creó un commit nuevo que hace lo contrario.
Ahora la historia cuenta todo, las luces y cómo se deshicieron.

Como nada de la historia compartida cambió, `git push` funcionó, y el siguiente `git pull` de Alex
trajo el cambio. Por eso revert es la forma de deshacer un commit que otros ya tienen. El
`git reset` de la próxima misión es para commits que solo tienes tú.

En el juego, `git revert` conserva el mensaje que Git sugiere (`Revert "Try strobe lights"`). En tu
propia computadora primero abre un editor con ese mensaje: guárdalo y ciérralo, o escribe
`git revert --no-edit HEAD~1` para saltarte el editor.

Comandos para recordar:

    $ git log --oneline     # encuentra el commit que quieres deshacer
    $ git revert HEAD~1     # un commit nuevo que lo deshace
    $ git push              # todos reciben el cambio con su pull
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, predice.",
        question="`main` tiene 4 commits ahora. Deshaces las luces con `git revert`. ¿Cuántos tendrá después?",
        options=("3: se quita el commit de las luces", "4: se reemplaza el commit de las luces", "5: se agrega un commit nuevo"),
        reveal="5. `git revert` nunca quita un commit. Agrega uno nuevo que hace lo contrario, así que la historia que Alex ya tiene sigue siendo cierta.",
    ),
    "look": kit.StepText(text="Encuentra el commit de las luces."),
    "revert": kit.StepText(text="Deshazlo con un commit nuevo."),
    "push": kit.StepText(text="Envía el cambio."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOOKED = "Del más nuevo al más viejo. El commit de las luces es el segundo desde arriba. Git puede nombrarlo desde `HEAD`: `HEAD~1` es un paso atrás por los padres, el commit justo antes del que estás."
NOT_LOOKED = "Primero lee la historia: `git log --oneline`."
NOT_REVERTED = "Las luces siguen en modo estroboscópico en tu `main`. Deshaz ese commit con uno nuevo: `git revert HEAD~1`."
BEHIND = "Tu `main` ya no tiene los commits compartidos; la nave nodriza todavía los tiene. `git pull` los trae de vuelta, y después haz revert."
PAUSED = "Hay un revert en pausa. Termínalo con `git revert --continue`, o cancélalo con `git revert --abort`."
ROUTE_LOST = "La ruta nocturna ya no está en tu `main`. Solo hay que deshacer las luces: `git revert HEAD~1` deshace ese único commit."
REVERTED = (
    "Un commit nuevo llegó arriba, el reflejo del de las luces. El commit de las luces sigue ahí, y la ruta nocturna también. "
    "`main` y `HEAD` subieron al commit nuevo; el pin de la nave nodriza y el de Alex no, porque todavía no lo tienen."
)
NOT_PUSHED = "El `main` de la nave nodriza todavía no tiene tu cambio: `git push`."
PUSHED = (
    "La nave nodriza tiene tu cambio: tu push solo agregó un commit encima de lo que ya tenía. Ahora Alex hace pull, y el "
    "cambio llega a su estación de la forma normal: las luces de todos vuelven a estar fijas."
)
REWRITTEN = (
    "El `main` de la nave nodriza ya no tiene los commits que Alex trajo: un push forzado reescribió la historia "
    "compartida. Vuelve a empezar la misión."
)
RESET_SHARED = (
    "Eso movió tu `main` hacia atrás, pero la nave nodriza y Alex todavía tienen esos commits. Para que la nave nodriza "
    "los olvide necesitarías `git push --force`, y eso rompe la copia de todos los demás. `git pull` los trae de vuelta; "
    "`git revert` deshace un commit sin reescribir nada."
)
FORCED = "`--force` reemplazó el `main` de la nave nodriza por el tuyo, y los commits que Alex trajo ya no están en él."
