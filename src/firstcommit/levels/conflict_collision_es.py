"""Collision in Spanish (`conflict_collision`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Colisión"
CARD = "Durante un conflicto de merge, pone en la carpeta de trabajo la versión del archivo del branch que llega; `--ours` pone la de tu branch. Luego `git add` marca el conflicto como resuelto. Durante un rebase, los dos pueden aparecer intercambiados."
SCENE = [
    "Las dos tripulaciones cambiaron la misma línea del plan de acople, y el archivo se partió.",
    "Un conflicto es una pregunta que Git no puede responder solo: ¿qué versión es la correcta?",
]

BRIEFING = """
Moviste el acople a la bahía 3 en `main`. Alex, en `scout`, lo movió a la bahía 4, y el commit de
Alex dice por qué: la bahía 3 está cerrada por reparaciones. Trae `scout` a `main` y responde el
conflicto con la bahía correcta.

La misión termina cuando hayas leído los dos lados del conflicto con `cat docking.txt`, y el último
commit de `main` tenga el trabajo de `scout` y acople en la bahía 4, sin marcadores de conflicto.
"""

HINTS = [
    "`git merge --no-edit scout` se detiene con `docking.txt` en conflicto; `cat docking.txt` muestra los dos lados entre marcadores.",
    "La bahía 4 es el lado de Alex, el que llega desde `scout`: `git restore --theirs docking.txt` lo conserva.",
    "`git add docking.txt` marca el conflicto como resuelto; luego `git commit --no-edit` termina el merge con el mensaje de Git.",
    "Cada línea de la misión, en orden:\n\n    $ git merge --no-edit scout\n    $ cat docking.txt\n    $ git restore --theirs docking.txt\n    $ git add docking.txt\n    $ git commit --no-edit",
]

DEBRIEF = """
El merge se detuvo porque los dos lados cambiaron la misma línea, y Git no puede saber cuál es la
correcta. `cat docking.txt` mostró los dos: el tuyo entre `<<<<<<<` y `=======`, el de Alex entre
`=======` y `>>>>>>>`. Git llama a tu lado *ours* y al lado que llega *theirs*. El commit de Alex
daba la razón, así que conservaste el lado de Alex con `git restore --theirs`, o escribiendo tú el
archivo. `git add` marcó el conflicto como resuelto, y
`git commit --no-edit` terminó el merge con dos padres.

Un conflicto es una pregunta, no una avería: no se perdió nada mientras el merge estaba en pausa,
y `git merge --abort` siempre estuvo disponible.

Comandos para recordar:

    $ git merge --no-edit scout          # se detiene si los dos lados cambiaron las mismas líneas
    $ cat docking.txt                    # lee los dos lados entre los marcadores
    $ git restore --theirs docking.txt   # conserva el lado que llega (--ours: el tuyo)
    $ git add docking.txt                # marca el conflicto como resuelto
    $ git commit --no-edit               # termina el merge
"""

STEPS = {
    "merge": kit.StepText(text="Trae `scout` a `main`."),
    "read": kit.StepText(text="Lee los dos lados del conflicto."),
    "choose": kit.StepText(text="Conserva la bahía que está abierta."),
    "add": kit.StepText(text="Marca el conflicto como resuelto."),
    "commit": kit.StepText(text="Termina el merge."),
}

NO_REPOSITORY = "Esta carpeta ya no es un repositorio: `.git` desapareció. Sal del nivel y vuelve a empezarlo para recuperarlo."
NOT_STARTED = "Trae `scout`: `git merge --no-edit scout`."
CONFLICT = "El merge se detuvo: `docking.txt` está en conflicto, y Git espera tu respuesta."
READ_BOTH = "Los dos lados están ahí: la bahía 3 es la tuya, la bahía 4 es la de Alex."
NOT_READ = "Lee los dos lados del conflicto: `cat docking.txt`."
MARKERS = "`docking.txt` todavía tiene los marcadores de conflicto. Conserva un lado: `git restore --theirs docking.txt`."
BAY_3 = "`docking.txt` acopla en la bahía 3, que está cerrada por reparaciones. El lado de Alex es el correcto: `git restore --theirs docking.txt`."
CHOSEN = "`docking.txt` acopla en la bahía 4, sin marcadores."
OTHER = "`docking.txt` debería decir `Dock at bay 4`, el lado que llega: `git restore --theirs docking.txt`."
NOT_ADDED = "Marca el conflicto como resuelto: `git add docking.txt`."
ADDED = "No queda ningún conflicto: el staging area tiene la bahía 4."
NOT_COMMITTED = "Termina el merge: `git commit --no-edit`."
NOT_BAY_4_COMMITTED = "El último commit de `main` no acopla en la bahía 4. Escribe la bahía 4 en `docking.txt` y luego agrégalo y haz commit otra vez."
BAY_3_COMMITTED = "El último commit de `main` acopla en la bahía 3, que está cerrada. Escribe la bahía 4 en `docking.txt` (`git restore --source=scout docking.txt`) y luego agrégalo y haz commit otra vez."
DONE = "El último commit de `main` tiene el trabajo de `scout` y acopla en la bahía 4."
ANSWER_FIRST = "Git no puede hacer commit mientras un archivo está en conflicto. Respóndele primero: elige un lado y luego haz `git add` del archivo."
SIDE = "Ese lado está ahora en la carpeta de trabajo. El conflicto sigue abierto hasta que hagas `git add` del archivo."
