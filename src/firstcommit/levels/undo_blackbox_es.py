"""Black box in Spanish (`undo_blackbox`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Caja negra"
CARD = "Lista por dónde estuvo `HEAD`, del más reciente al más antiguo, como `HEAD@{0}`, `HEAD@{1}` y así. Los commits que ya no tienen ninguna etiqueta se pueden encontrar ahí y volver a etiquetar."
SCENE = [
    "Alarma en la cubierta de motores: dos días de trabajo en los propulsores desaparecieron con su branch.",
    "No se hizo push de nada. Pero el registro de vuelo estuvo funcionando todo el tiempo.",
]

BRIEFING = """
Anoche guardaste dos días de ajustes de los propulsores en commits de un branch `thrusters`.
Después, con mucho sueño, pasaste a `main` y borraste el branch con `git branch -D`. Nunca se hizo
push de él, y la revisión es esta mañana.

La misión termina cuando tu repositorio vuelva a tener un branch `thrusters` con los dos commits, y
la nave nodriza también tenga `thrusters`, con su `main` intacto.
"""

HINTS = [
    "Esto es la bóveda, los branches y este capítulo: commits sin etiqueta, una etiqueta, y un push por nombre.",
    "El reflog lista por dónde estuvo `HEAD`: la línea antes del paso a `main` nombra el último commit del branch. Una etiqueta sobre él recupera los dos commits.",
    "Cada línea de la misión, en orden:\n\n    $ git reflog\n    $ git branch thrusters HEAD@{1}\n    $ git push -u origin thrusters",
]

DEBRIEF = """
`git branch -D` quitó una etiqueta, no los commits: se quedaron en Git como fantasmas sin
etiqueta. `git reflog` mostró cada movimiento de `HEAD`, y `HEAD@{1}`, donde estaba un movimiento
antes del paso a `main`, era el último commit del branch. `git branch thrusters HEAD@{1}` le devolvió
su etiqueta, con los dos commits, y `git push -u origin thrusters` los envió para la revisión.

El reflog vive solo en tu repositorio, y por defecto guarda entradas como estas, de commits sin
etiqueta, durante más o menos un mes. La nave nodriza y cada clone tienen su propio registro.

Comandos para recordar:

    $ git reflog                       # por dónde estuvo HEAD
    $ git branch thrusters HEAD@{1}    # una etiqueta sobre un commit del reflog
    $ git push -u origin thrusters     # y que suba
"""

STEPS = {
    "rescued": kit.StepText(text="Tu repositorio tiene un branch `thrusters` con los dos commits."),
    "launched": kit.StepText(text="La nave nodriza tiene `thrusters` con los dos commits, y su `main` está intacto."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_RESCUED = "Tu repositorio no tiene ningún branch `thrusters` con los dos commits."
RESCUED = "`thrusters` vuelve a tener los dos commits."
NOT_LAUNCHED = "La nave nodriza no tiene ningún `thrusters` con los dos commits."
LAUNCHED = "La nave nodriza tiene `thrusters` con los dos commits, y su `main` está intacto."
ERASED = "Los commits de los propulsores se perdieron para siempre: se borró la caja negra y Git los eliminó. Vuelve a empezar la misión."
MAIN_TOUCHED = "El `main` de la nave nodriza ahora tiene los commits de los propulsores, sin revisión. Vuelve a empezar la misión."
WIPE = (
    "Eso limpia la caja negra de Git: los commits sin etiqueta pueden borrarse para siempre cuando el reflog los olvida. "
    "Primero ponles una etiqueta."
)
