"""Black box in Spanish (`undo_blackbox`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Turno de noche"
CARD = "Lista por dónde estuvo `HEAD`, del más reciente al más antiguo, como `HEAD@{0}`, `HEAD@{1}` y así. Los commits a los que ya no lleva ningún branch se pueden encontrar ahí y volver a nombrar."
SCENE = [
    "Alarma en la cubierta de motores: dos noches de trabajo en los propulsores desaparecieron con su branch. No se hizo push de nada, pero `HEAD` lleva un log de movimientos. Cuidado: el log de movimientos cuenta hacia atrás desde ahora, así que sus números no son los de la misión anterior.",
]

BRIEFING = """
Dos noches de ajustes de los propulsores quedaron en commits de un branch `thrusters`. Con mucho
sueño, pasaste a `main` y borraste el branch con `git branch -D thrusters`: se fue el nombre, y los
commits se quedaron sin nombre. Esta mañana trajiste con pull el commit de Alex `Note the free dock`.
Recupera `thrusters` y súbelo al remoto (la nave nodriza) antes de la revisión.
"""

HINTS = [
    "Esto es branches y este sector: commits a los que no lleva ningún branch, un nombre y un push por nombre. Un branch se puede enviar desde cualquier lugar, por su nombre: `git push -u origin thrusters` (o `git push origin thrusters`).",
    "El log de movimientos lista por dónde estuvo `HEAD`. Busca ahí tu último commit de los propulsores; un branch sobre él recupera los dos. Su `HEAD@{n}` y el hash al principio de su línea sirven los dos. Puedes enviar un branch sin cambiarte a él.",
    "Cada línea de la misión, en orden (el hash de esa línea sirve igual que `HEAD@{2}`):\n\n    $ git reflog\n    $ git branch thrusters HEAD@{2}\n    $ git push -u origin thrusters",
]

DEBRIEF = """
`git branch -D` quitó un nombre, no los commits. `git reflog` mostró cada movimiento de `HEAD`, y
`HEAD@{2}`, dos movimientos atrás, era el último commit de los propulsores. `git branch thrusters
HEAD@{2}` le devolvió su nombre, con los dos commits, y `git push -u origin thrusters` los envió
para la revisión.

Comandos para recordar:

    $ git reflog                       # por dónde estuvo HEAD
    $ git branch thrusters HEAD@{2}    # un nombre en un commit del log de movimientos
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
ERASED = "Los commits de los propulsores se perdieron para siempre: se borró el log de movimientos y Git los eliminó. Vuelve a empezar la misión."
MAIN_TOUCHED = "El `main` de la nave nodriza ahora tiene los commits de los propulsores, sin revisión. Vuelve a empezar la misión."
WIPE = "Eso limpia los commits a los que no lleva ningún branch: se pueden borrar para siempre cuando el log de movimientos los olvida. Primero ponles un nombre."
