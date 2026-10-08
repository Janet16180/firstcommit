"""Push refused in Spanish (`mothership_refused`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Push rechazado"
CARD = "Trae los commits del remoto a tu branch y junta las dos historias con un commit de merge. `--rebase`, en cambio, vuelve a aplicar tus commits encima de los del remoto."
SCENE = [
    "Tu cápsula está lista en la plataforma de lanzamiento, y Alex también está trabajando.",
    "Cuando dos tripulaciones envían cápsulas al mismo lugar, la nave nodriza se queda con la primera y no acepta soltarla.",
]

BRIEFING = """
Hiciste el commit de la ruta esta mañana. Alex acaba de hacer push de un informe a la nave
nodriza. Sube tu commit y conserva el de Alex.

La misión termina cuando hayas visto tu push rechazado, el commit de Alex esté en tu `main` y la
nave nodriza tenga los dos commits.
"""

HINTS = [
    "Un push rechazado no pierde nada: primero trae el commit de Alex a tu `main` y luego vuelve a hacer push.",
    "`git pull --no-rebase` junta las dos historias con un commit de merge; `git pull --rebase` pone tu commit encima del de Alex. Luego `git push`.",
    "Cada línea de la misión, en orden:\n\n    $ git push\n    $ git pull --no-rebase\n    $ git push",
]

DEBRIEF = """
Git rechazó tu push porque la nave nodriza tenía un commit que tu `main` no tenía: aceptar el
tuyo habría dejado fuera el de Alex. No se perdió nada. `git pull` con `--no-rebase` juntó las dos
historias en un commit de merge, o con `--rebase` volvió a aplicar tu commit encima del de Alex;
de las dos formas tu `main` quedó con ambos, y el push pasó.

Los commits de merge tienen su propio capítulo: Colisiones.

Comandos para recordar:

    $ git pull --no-rebase   # trae los commits del remoto, unidos con un commit de merge
    $ git pull --rebase      # o vuelve a aplicar tus commits encima de los del remoto
    $ git push
"""

STEPS = {
    "push": kit.StepText(text="Intenta subir tu commit."),
    "pull": kit.StepText(text="Trae el commit de Alex a tu `main`."),
    "send": kit.StepText(text="Sube los dos commits."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
WAITING = "Alex todavía está en camino. Espera un momento al informe."
BOUNCED = "Git rechazó el push: la nave nodriza tiene el commit de Alex, y tu `main` no."
NOT_BOUNCED = "Sube tu commit: `git push`."
JOINED = "Tu `main` tiene el commit de Alex y el tuyo."
NOT_JOINED = "Tu `main` todavía no tiene el commit de Alex. Tráelo: `git pull`."
SENT = "La nave nodriza tiene el commit de Alex y el tuyo."
NOT_SENT = "Sube la historia unida: `git push`."
ALEX_DROPPED = (
    "El `main` de la nave nodriza ya no tiene el commit de Alex: un push forzado lo reemplazó por el tuyo. En el trabajo, eso "
    "borra el trabajo de alguien del equipo. Vuelve a empezar la misión."
)
CHOOSE = (
    "Git se detuvo: tanto tú como Alex agregaron commits, así que pregunta cómo juntarlos. `git pull --no-rebase` junta las dos historias "
    "con un commit de merge; `git pull --rebase` vuelve a aplicar tu commit encima del de Alex. Aquí sirve cualquiera de los dos."
)
FORCED = "`--force` reemplazó el `main` de la nave nodriza por el tuyo, y el commit de Alex ya no está en él. Un push rechazado nunca lo necesita."
