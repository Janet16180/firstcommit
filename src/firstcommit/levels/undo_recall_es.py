"""Recall the capsule in Spanish (`undo_recall`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Retira la cápsula"
CARD = "Crea un commit nuevo que deshace uno anterior. El commit anterior se queda en la historia, así que es seguro en un branch que otros ya trajeron con pull."
SCENE = [
    "Una cápsula que lanzaste puso las luces de la estación en modo estroboscópico, y Alex ya la tiene.",
    "Las cápsulas que otros ya trajeron se quedan en la cadena. Para retirar una, envías una cápsula nueva que la deshace.",
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
`git revert HEAD~1` no quitó el commit de las luces: creó un commit nuevo que hace lo contrario, y
la ruta nocturna que vino después se quedó. Ahora la historia cuenta todo: las luces, y cómo se
deshicieron.

Como nada de la historia compartida cambió, `git push` funcionó como cualquier otro push, y el
siguiente `git pull` de Alex llevó el cambio a su estación. Por eso revert es la herramienta para
un commit que otros ya tienen. Mover `main` hacia atrás con `git reset` habría necesitado un push
forzado, y eso rompe la copia de todos los demás.

Comandos para recordar:

    $ git log --oneline     # encuentra el commit que quieres deshacer
    $ git revert HEAD~1     # un commit nuevo que lo deshace
    $ git push              # todos reciben el cambio con su pull
"""

STEPS = {
    "look": kit.StepText(text="Encuentra en la historia el commit de las luces."),
    "revert": kit.StepText(text="Deshaz las luces con un commit nuevo, y conserva la ruta nocturna."),
    "push": kit.StepText(text="Envía el cambio a la nave nodriza."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOOKED = "`git log` lista el commit de las luces, con la ruta nocturna después."
NOT_LOOKED = "Primero lee la historia: `git log --oneline`."
NOT_REVERTED = "Las luces siguen en modo estroboscópico en tu `main`. Deshaz ese commit con uno nuevo: `git revert HEAD~1`."
BEHIND = "Tu `main` ya no tiene los commits compartidos; la nave nodriza todavía los tiene. `git pull` los trae de vuelta, y después haz revert."
PAUSED = "Hay un revert en pausa. Termínalo con `git revert --continue`, o cancélalo con `git revert --abort`."
ROUTE_LOST = "La ruta nocturna ya no está en tu `main`. Solo hay que deshacer las luces: `git revert HEAD~1` deshace ese único commit."
REVERTED = "Tu `main` tiene un commit que deshace las luces, y toda la historia compartida sigue ahí."
NOT_PUSHED = "El `main` de la nave nodriza todavía no tiene tu cambio: `git push`."
PUSHED = "El `main` de la nave nodriza tiene tu cambio, así que todos lo recibirán en su próximo pull."
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
