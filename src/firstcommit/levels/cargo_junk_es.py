"""Junk bay in Spanish (`cargo_junk`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Bahía de chatarra"
CARD = "Un archivo de nombres y patrones que Git ignora: `git status` deja de listarlos y `git add .` se los salta. Los archivos siguen en tu disco."
SCENE = [
    "El simulador de saltos funcionó toda la noche, y cada vez que funciona escribe un montón de archivos de resultados.",
    "Los archivos generados se quedan en tu disco, pero nunca van en un commit.",
]

BRIEFING = """
El simulador de saltos funcionó durante la noche y llenó `sim-output/` de archivos de resultados,
uno por ejecución. Se vuelven a crear en cada ejecución, así que nunca van en un commit. Tu
trabajo de verdad es el nuevo rumbo en `nav.cfg`.

La misión termina cuando hayas mirado con `git status`, un archivo `.gitignore` le diga a Git que
ignore `sim-output/`, y tanto `.gitignore` como `nav.cfg` estén en el staging area, sin nada de
`sim-output/`.
"""

HINTS = [
    "Un archivo llamado `.gitignore` lista lo que Git ignora, un nombre o patrón por línea: `sim-output/` ignora toda la carpeta.",
    'Escríbelo desde la terminal: `echo "sim-output/" > .gitignore`, y después agrega al staging area la regla y tu cambio.',
    'Cada línea de la misión, en orden:\n\n    $ git status\n    $ echo "sim-output/" > .gitignore\n    $ git add .gitignore nav.cfg',
]

DEBRIEF = """
`.gitignore` le dijo a Git que ignore todo lo que hay en `sim-output/`. Los archivos siguen en tu
disco; `git status` dejó de listarlos, y `git add .` se los salta, así que no pueden colarse en un
commit por accidente.

También agregaste `.gitignore` al staging area. Cuando esté en un commit, todos los que trabajan
en el proyecto tendrán la misma regla, y los resultados del simulador de nadie llegarán a la nave
nodriza. En los proyectos de verdad, las carpetas de compilación, los logs y las dependencias
descargadas reciben el mismo trato.

Comandos para recordar:

    $ echo "sim-output/" > .gitignore   # ignora una carpeta de archivos generados
    $ git add .gitignore                # comparte la regla con la tripulación
"""

STEPS = {
    "look": kit.StepText(text="Averigua qué dejó el simulador en la carpeta de trabajo."),
    "ignore": kit.StepText(text="Dile a Git que ignore `sim-output/`."),
    "stage": kit.StepText(text="Agrega al staging area la regla y tu cambio, y nada más."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
LOOKED = "`git status` lista `sim-output/` como sin seguimiento, junto a tu cambio en `nav.cfg`."
NOT_LOOKED = "Mira primero: `git status` muestra lo que el simulador dejó en la carpeta de trabajo."
NOT_IGNORED = 'Git todavía no ignora `sim-output/`. Escribe su nombre en un archivo llamado `.gitignore`: `echo "sim-output/" > .gitignore`.'
IGNORED = "`.gitignore` nombra `sim-output/`: Git ignora los resultados del simulador."
JUNK_ABOARD = "Hay archivos de `sim-output/` en el staging area. `git restore --staged sim-output` los saca del staging area; los archivos se quedan en tu disco."
NOT_STAGED = "Agrega al staging area la regla y tu cambio: `git add .gitignore nav.cfg`. Ahora que los resultados están ignorados, `git add .` también sirve."
JUNK_COMMITTED = (
    "Ya hay archivos de `sim-output/` en un commit, así que están en la historia de este repositorio. Deshacer un commit "
    "llega en un capítulo posterior: vuelve a empezar la misión."
)
STAGED = "`.gitignore` y `nav.cfg` están en el staging area, y nada de `sim-output/` lo está."
WHY_IGNORE = (
    "Todo lo que hay en `sim-output/` es generado, y aparece como sin seguimiento. Un `git add .` ahora se llevaría cada archivo al "
    "próximo commit, y cada copia del proyecto los descargaría, para siempre. Un `.gitignore` los deja fuera."
)
JUNK_STAGED = (
    "Eso también agregó al staging area los resultados del simulador: cada archivo de `sim-output/`. "
    "`git restore --staged sim-output` los saca del staging area y conserva los archivos; después, dile a Git que los ignore."
)
IGNORE_FIELD = "`.gitignore` está en su lugar: Git ignora los archivos que nombra. Siguen en tu disco; `git status` y `git add .` se los saltan."
REGENERATED = "El simulador vuelve a crear esos archivos en su próxima ejecución. Mejor pídele a Git que los ignore: así pueden quedarse en tu disco."
