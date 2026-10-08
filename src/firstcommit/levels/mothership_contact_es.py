"""Make contact in Spanish (`mothership_contact`)."""

from firstcommit import kit

TITLE = "Primer contacto"
CARD = "Da un nombre corto, como `origin`, a la dirección de otro repositorio dentro del tuyo. No se envía nada: solo anota el nombre."
SCENE = [
    "La nave nodriza orbita sobre la base. Guarda una copia del trabajo de todas las tripulaciones.",
    "Antes de poder enviarle nada, tu repositorio necesita su dirección, con un nombre corto.",
]

BRIEFING = """
Tu base tiene dos commits, y la nave nodriza los espera en `../github/project.git`. Primero,
establece contacto: dale a esa dirección el nombre `origin` en tu repositorio.

La misión termina cuando `origin` apunte a `../github/project.git` y hayas listado los remotos
con `git remote -v`.
"""

HINTS = [
    "`git remote add` recibe un nombre y luego la dirección: `git remote add origin ../github/project.git`.",
    "`git remote -v` lista el nombre de cada remoto con su dirección.",
    "Cada línea de la misión, en orden:\n\n    $ git remote add origin ../github/project.git\n    $ git remote -v",
]

DEBRIEF = """
`origin` es ahora un nombre para la dirección de la nave nodriza, guardado en la configuración de
tu repositorio. No viajó nada: la nave nodriza sigue vacía, y tus commits solo están aquí.
Enviarlos es la próxima misión.

En el trabajo, la dirección es la que GitHub muestra para tu proyecto, como
`https://github.com/<you>/<project>.git`; `origin` es el nombre que todo el mundo usa para ella.

Comandos para recordar:

    $ git remote add origin ../github/project.git   # da nombre a la dirección de la nave nodriza
    $ git remote -v                                 # lista los remotos y sus direcciones
"""

STEPS = {
    "guess": kit.StepText(
        text="Primero, haz tu predicción.",
        question="Cuando tu repositorio conozca la dirección de la nave nodriza, ¿qué tendrá la nave nodriza?",
        options=("Tus dos commits", "Nada todavía", "Una copia de tus archivos"),
        reveal="Nada todavía: nombrar un remoto solo anota su dirección en tu repositorio. Nada viaja hasta que lo envías.",
    ),
    "remote": kit.StepText(text="Llama `origin` a la dirección de la nave nodriza."),
    "list": kit.StepText(text="Lista los remotos que conoce tu repositorio."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NO_REMOTE = "Tu repositorio todavía no conoce ningún remoto. Da nombre a la dirección de la nave nodriza: `git remote add origin ../github/project.git`."
OTHER_NAME = "La dirección de la nave nodriza tiene otro nombre. En esta misión se llama `origin`: `git remote add origin ../github/project.git`."
WRONG_URL = "`origin` apunta a otra dirección. La nave nodriza está en `../github/project.git`: `git remote set-url origin ../github/project.git` la cambia."
CONTACT = "`origin` ya es el nombre de la dirección de la nave nodriza."
LISTED = "`git remote -v` lista `origin` con su dirección, una vez para traer y otra para enviar."
NOT_LISTED = "Ahora lista los remotos con `git remote -v`."
REMOTE_EXISTS = "`origin` ya existe. Para cambiar su dirección, usa `git remote set-url origin` con la nueva dirección."
HTTPS_URL = (
    "En este juego la nave nodriza es una carpeta junto a tu base, `../github/project.git`. En el trabajo la dirección "
    "empezaría por `https://`; aquí, `git remote set-url origin ../github/project.git` la apunta a la nave nodriza."
)
