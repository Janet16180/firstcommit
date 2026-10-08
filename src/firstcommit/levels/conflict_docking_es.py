"""Docking collision in Spanish (`conflict_docking`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Colisión en el acople"
CARD = "Hace commit con el mensaje que Git preparó, sin pedir uno: durante un merge, el mensaje del propio merge. Termina un merge una vez que agregaste cada conflicto."
SCENE = [
    "En plena aproximación: tú y Alex reescribieron la línea del acople, y Alex envió la suya primero.",
    "Lleva el trabajo de las dos tripulaciones a la nave nodriza, con la bahía segura.",
]

BRIEFING = """
En plena aproximación, escribiste la lista de verificación y cambiaste el plan de acople a la
bahía 5, en un solo commit. Alex cambió la misma línea a la bahía 4 e hizo push primero: la bahía 5
perdió sus abrazaderas. Lleva el trabajo de las dos tripulaciones a la nave nodriza, acoplando en
la bahía segura.

La misión termina cuando tu `main` tenga el commit de Alex y tu lista de verificación, y
`docking.txt` allí acople en la bahía 4 sin marcadores de conflicto, y el `main` de la nave nodriza
sea igual al tuyo.
"""

HINTS = [
    "Es la nave nodriza y este capítulo: un push rechazado, un pull, un conflicto que responder y un push.",
    "Tu push se rechaza hasta que tu `main` tenga el commit de Alex. Haz pull, responde el conflicto con la bahía de Alex, agrega, haz commit y push; si Alex volvió a avanzar, haz pull una vez más.",
]

DEBRIEF = """
Tu push rebotó: la nave nodriza tenía el commit de Alex. El pull se detuvo en la línea del acople,
porque los dos lados la cambiaron, así que leíste los dos, conservaste la bahía 4 de Alex,
agregaste el archivo y terminaste el pull: `git commit --no-edit` después de un merge,
`git rebase --continue` después de un rebase. Tu lista de verificación llegó de las dos formas.
Para entonces Alex había hecho push otra vez, así que tu siguiente push también rebotó; un pull más
juntó ese commit sin conflicto, y el push pasó.

Así trabaja un equipo con mucho movimiento: pull, responder lo que Git pregunta, push, y otro pull
cuando alguien fue más rápido. Nunca uses `--force` en un branch compartido.
"""

STEPS = {
    "joined": kit.StepText(text="Tu `main` tiene el commit de Alex y tu lista de verificación, y `docking.txt` allí acopla en la bahía 4 sin marcadores."),
    "sent": kit.StepText(text="El `main` de la nave nodriza es igual al tuyo."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
ALEX_DROPPED = "El `main` de la nave nodriza ya no tiene el trabajo de Alex: un push forzado lo reemplazó. Vuelve a empezar la misión."
NOT_JOINED = "Tu `main` todavía no tiene el commit de Alex y tu lista de verificación."
CHECKLIST_LOST = "Tu lista de verificación ya no está en ningún commit: se perdió. Vuelve a empezar la misión."
PAUSED = "Hay un merge en pausa: responde el conflicto, agrega el archivo y haz commit."
NOT_BAY_4 = "Tu `main` tiene el commit de Alex y tu lista de verificación, pero allí `docking.txt` no acopla en la bahía 4 sin marcadores."
JOINED = "Tu `main` tiene el commit de Alex y tu lista de verificación, y acopla en la bahía 4."
NOT_SENT = "El `main` de la nave nodriza todavía no es igual al tuyo."
SENT = "El `main` de la nave nodriza es el tuyo."
FORCED = "`--force` reemplazó el `main` de la nave nodriza por el tuyo. En un equipo, eso borra el trabajo de alguien."
