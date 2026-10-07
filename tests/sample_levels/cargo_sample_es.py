"""The sample level's texts in Spanish (`cargo_sample`), for the game's own tests."""

from firstcommit import kit

TITLE = "Di hola"
BRIEFING = "Haz un commit de `hello.txt` en la rama `{{branch}}`."
HINTS = [
    "Un commit guarda lo que hay en el área de preparación.",
    "Prepara el archivo y luego haz el commit.",
    "Escribe `git add hello.txt` y después `git commit -m 'Say hello'`.",
]
DEBRIEF = "`hello.txt` ya está en un commit en `{{branch}}`."
CARD = "Copia un archivo al área de preparación."
SCENE = [
    "Tres lugares: la carpeta de trabajo, el área de preparación y el repositorio.",
    "`git add` copia un archivo al área de preparación.",
]
STEPS = {
    "look": kit.StepText(text="Mira el repositorio con `git status`."),
    "stage": kit.StepText(text="Prepara `hello.txt`."),
    "branch": kit.StepText(text="Encuentra la rama.", question="¿Qué rama es `{{branch}}`?", placeholder="un nombre de rama"),
}
HELLO_STAGED = "Hello está preparado."
STAGED = "Preparado."
NOT_STAGED = "Todavía no está preparado."
RIGHT = "Correcto."
LOOK = "Mira la primera línea de `git status`."
COMMITTED = "Hecho el commit."
NOT_COMMITTED = "`hello.txt` todavía no está en ningún commit."
