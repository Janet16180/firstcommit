"""Launch in Spanish (`mothership_launch`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Lanzamiento"
CARD = "Envía los commits de `main` a `origin` y convierte `origin/main` en su upstream, así que después un `git push` a secas sabe adónde ir."
SCENE = [
    "Un push sube tus cápsulas a la nave nodriza.",
    "Solo vuelan las cápsulas. Un cambio que no está en ninguna cápsula se queda en tierra.",
]

BRIEFING = """
Tu base conoce la nave nodriza como `origin`, y la nave nodriza sigue vacía. Lanza tus dos
cápsulas y luego averigua qué envía un push cuando tu trabajo no está en una cápsula.

La misión termina cuando el `main` de la nave nodriza tenga tus commits, un cambio en `route.txt`
haya subido solo después de su commit y lo hayas enviado con un `git push` a secas.
"""

HINTS = [
    "El primer push de un branch dice adónde va: `git push -u origin main`.",
    'Haz el commit del cambio antes del push: `git commit -am "Add the Phobos stop"` y luego `git push`.',
    'Cada línea de la misión, en orden:\n\n    $ git push -u origin main\n    $ echo "Stop: Phobos" >> route.txt\n    $ git push\n    $ git commit -am "Add the Phobos stop"\n    $ git push',
]

DEBRIEF = """
`git push -u origin main` envió tus dos commits a la nave nodriza y convirtió `origin/main` en el
upstream de tu `main`. El push con el cambio no envió nada nuevo, porque el cambio no estaba en
ningún commit. Después del commit, un `git push` a secas lo subió.

Comandos para recordar:

    $ git push -u origin main   # el primer push de main
    $ git push                  # envía los commits nuevos al upstream
"""

STEPS = {
    "launch": kit.StepText(text="Lanza tus commits a la nave nodriza."),
    "guess": kit.StepText(
        text="Primero, haz tu predicción.",
        question="Editas `route.txt` y haces push sin hacer commit. ¿Qué recibe la nave nodriza?",
        options=("El `route.txt` editado", "Nada nuevo"),
        reveal="Nada nuevo: un push envía commits, y el cambio no está en ninguno. Primero haz el commit.",
    ),
    "edit": kit.StepText(text="Agrega una parada a la ruta."),
    "fizzle": kit.StepText(text="Haz push con el cambio fuera de todo commit."),
    "commit": kit.StepText(text="Haz el commit del cambio."),
    "send": kit.StepText(text="Sube el commit nuevo."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NO_UPSTREAM = "Ese push se detuvo: `main` todavía no tiene upstream. El primer push lo nombra: `git push -u origin main`."
LAUNCHED = "El `main` de la nave nodriza tiene tus commits, y `origin/main` es el upstream de tu `main`."
NOT_LAUNCHED = "Lanza tus commits: `git push -u origin main`."
NO_UPSTREAM_SET = "La nave nodriza tiene tus commits, pero `main` todavía no tiene upstream: `git push -u origin main` lo configura."
EDITED = "`route.txt` tiene una línea nueva, todavía en ningún commit."
NOT_EDITED = 'Agrega una parada a la ruta: `echo "Stop: Phobos" >> route.txt`.'
FIZZLED = "El push no envió nada nuevo: el cambio no está en ningún commit, así que no había nada que enviar."
NOT_FIZZLED = "Ahora haz push, con el cambio todavía fuera de todo commit: `git push`."
COMMITTED_EDIT = "El cambio ya está en un commit, por delante de `origin/main`."
EDIT_NOT_COMMITTED = 'Haz el commit del cambio: `git commit -am "Add the Phobos stop"`.'
SENT = "El `main` de la nave nodriza tiene el commit del cambio."
NOT_SENT = "Sube el commit nuevo: `git push`."
