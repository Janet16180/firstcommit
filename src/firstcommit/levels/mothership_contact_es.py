"""Make contact in Spanish (`mothership_contact`)."""

from firstcommit import kit

TITLE = "Primer contacto"
CARD = "Da un nombre corto, como `origin`, a la dirección de otro repositorio dentro del tuyo. No se envía nada: solo anota el nombre."
SCENE = [
    "La nave nodriza orbita sobre la base. Guarda una copia del trabajo de todas las tripulaciones.",
    "Antes de poder enviarle nada, tu repositorio necesita su dirección, con un nombre corto.",
]

BRIEFING = """
Tu base tiene dos commits, y la nave nodriza los espera en `../github.com/moonbase/project.git`. Primero,
establece contacto: dale a esa dirección el nombre `origin` en tu repositorio.

La misión termina cuando `origin` apunte a `../github.com/moonbase/project.git` y hayas listado los remotos
con `git remote -v`.

En este juego la nave nodriza es una carpeta junto a tu proyecto. En el trabajo, la misma dirección se ve
así: `https://github.com/moonbase/project.git`.
"""

HINTS = [
    "`git remote add` recibe un nombre y luego la dirección: `git remote add origin ../github.com/moonbase/project.git`.",
    "`git remote -v` lista el nombre de cada remoto con su dirección.",
    "Cada línea de la misión, en orden:\n\n    $ git remote add origin ../github.com/moonbase/project.git\n    $ git remote -v",
]

DEBRIEF = """
`origin` es ahora un nombre para la dirección de la nave nodriza, guardado en la configuración de
tu repositorio. No viajó nada: la nave nodriza sigue vacía, y tus commits solo están aquí.
Enviarlos es la próxima misión.

En este juego la nave nodriza es una carpeta junto a tu proyecto. En el trabajo, la misma dirección
se ve así: `https://github.com/moonbase/project.git`, la que GitHub muestra para el proyecto;
`origin` es el nombre que todo el mundo usa para ella.

Comandos para recordar:

    $ git remote add origin ../github.com/moonbase/project.git   # da nombre a la dirección de la nave nodriza
    $ git remote -v                                              # lista los remotos y sus direcciones
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
NO_REMOTE = "Tu repositorio todavía no conoce ningún remoto. Da nombre a la dirección de la nave nodriza: `git remote add origin ../github.com/moonbase/project.git`."
OTHER_NAME = "La dirección de la nave nodriza tiene otro nombre. En esta misión se llama `origin`: `git remote add origin ../github.com/moonbase/project.git`."
WRONG_URL = "`origin` apunta a otra dirección. La nave nodriza está en `../github.com/moonbase/project.git`: `git remote set-url origin ../github.com/moonbase/project.git` la cambia."
CONTACT = "`origin` ya es el nombre de la dirección de la nave nodriza."
LISTED = "`git remote -v` lista `origin` con su dirección, una vez para traer y otra para enviar."
NOT_LISTED = "Ahora lista los remotos con `git remote -v`."
REMOTE_EXISTS = "`origin` ya existe. Para cambiar su dirección, usa `git remote set-url origin` con la nueva dirección."
AT_WORK = "En este juego la nave nodriza es una carpeta junto a tu proyecto. En el trabajo, la misma dirección se ve así: `https://github.com/moonbase/project.git`."
HTTPS_URL = (
    "En este juego la nave nodriza es una carpeta junto a tu proyecto, `../github.com/moonbase/project.git`. En el trabajo, la misma dirección "
    "se ve así: `https://github.com/moonbase/project.git`; aquí, `git remote set-url origin ../github.com/moonbase/project.git` la vuelve a apuntar a la nave nodriza."
)
