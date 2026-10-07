"""The sample level's texts in Spanish (`cargo_sample`), for the game's own tests."""

from firstcommit import kit

TITLE = "Di hola"
BRIEFING = "Haz un commit de `hello.txt` en el branch `{{branch}}`."
HINTS = [
    "Un commit guarda lo que hay en el staging area.",
    "Agrega el archivo al staging area y luego haz el commit.",
    "Escribe `git add hello.txt` y después `git commit -m 'Say hello'`.",
]
DEBRIEF = "`hello.txt` ya está en un commit en `{{branch}}`."
CARD = "Copia un archivo al staging area."
SCENE = [
    "Tres lugares: la carpeta de trabajo, el staging area y el repositorio.",
    "`git add` copia un archivo al staging area.",
]
STEPS = {
    "look": kit.StepText(text="Mira el repositorio con `git status`."),
    "stage": kit.StepText(text="Agrega `hello.txt` al staging area."),
    "branch": kit.StepText(text="Encuentra el branch.", question="¿Qué branch es `{{branch}}`?", placeholder="un nombre de branch"),
}
HELLO_STAGED = "Hello está en el staging area."
STAGED = "En el staging area."
NOT_STAGED = "Todavía no está en el staging area."
RIGHT = "Correcto."
LOOK = "Mira la primera línea de `git status`."
COMMITTED = "Commit hecho."
NOT_COMMITTED = "`hello.txt` todavía no está en ningún commit."
