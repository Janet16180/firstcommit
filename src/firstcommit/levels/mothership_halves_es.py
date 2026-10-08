"""Two halves of a ship in Spanish (`mothership_halves`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Dos mitades de una nave"
CARD = "Trae los commits nuevos del remoto a tu branch: un fetch y luego un merge (o solo un avance de tu etiqueta cuando no tienes nada nuevo)."
SCENE = [
    "La nave está a medio construir. Tú terminas la navegación; Alex, en otra estación, termina los motores.",
    "Cada uno envía su mitad a la nave nodriza, y cada uno trae la del otro.",
]

BRIEFING = """
El armazón de la nave está en la nave nodriza. La navegación en `nav.cfg` es tuya, y tu cambio está
listo pero sin commit. Los motores en `engine.cfg` son de Alex, que los está terminando ahora mismo
en otra estación.

La misión termina cuando tu navegación tenga commit y esté en la nave nodriza, y tu `main` tenga
también los motores de Alex: la nave entera.
"""

HINTS = [
    "Tu mitad viaja como un commit: haz commit de `nav.cfg` y luego push.",
    "Cuando Alex haya hecho push, `git pull` trae su mitad a tu `main`.",
    'Cada línea de la misión, en orden:\n\n    $ git commit -am "Set the navigation"\n    $ git push\n    $ git pull',
]

DEBRIEF = """
Tú y Alex trabajaron al mismo tiempo, cada uno en un archivo distinto. Tu push llegó primero a la
nave nodriza, así que el push de Alex se rechazó hasta que Alex hizo pull; ese pull juntó las dos
mitades en un commit de merge sin conflicto, porque los cambios tocaban archivos distintos. Luego
tu `git pull` trajo ese merge a tu `main`, y las dos estaciones tienen la nave entera.

Esa es la gracia de Git para un equipo: dos personas, al mismo tiempo, en partes distintas, y Git
junta las piezas.

Comandos para recordar:

    $ git commit -am "Set the navigation"   # tu mitad, en un commit
    $ git push                              # a la nave nodriza
    $ git pull                              # y la otra mitad de vuelta
"""

STEPS = {
    "commit": kit.StepText(text="Haz commit de tu mitad de la nave."),
    "push": kit.StepText(text="Envía tu mitad a la nave nodriza."),
    "pull": kit.StepText(text="Trae la mitad de Alex a tu `main`."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_COMMITTED = 'Tu navegación todavía no está en un commit: `git commit -am "Set the navigation"`.'
COMMITTED = "Tu navegación está en un commit, lista para viajar."
NOT_PUSHED = "La nave nodriza todavía no tiene tu navegación: `git push`."
PUSHED = "La nave nodriza tiene tu navegación."
WAITING = "Alex todavía está terminando los motores. Espera un momento a su push."
NOT_PULLED = "Tu `main` todavía no tiene los motores de Alex: `git pull`."
WHOLE = "Tu `main` tiene la nave entera: tu navegación y los motores de Alex."
TWO_HALVES = (
    "La nave entera está en tu estación: tu navegación y los motores de Alex. Dos personas trabajaron al mismo tiempo en "
    "partes distintas, y Git juntó las piezas."
)
