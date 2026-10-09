"""Deleting isn't erasing in Spanish (`undo_erasing`), written with docs/i18n-glossary.md."""

from firstcommit import kit

TITLE = "Borrar no es olvidar"
CARD = "Imprime el archivo como lo guardó el commit anterior a `HEAD`, aunque un commit posterior lo haya quitado."
SCENE = [
    "En el staging area (el muelle de carga), dejaste una contraseña fuera de un commit con `git restore --staged`.",
    "Anoche una se coló: `keys.txt`, con la contraseña de la esclusa. La quitaste en el commit siguiente e hiciste push de los dos, y Alex ya hizo pull.",
]

BRIEFING = """
Anoche un commit se llevó las llaves de la esclusa por error, así que las quitaste en el commit
siguiente. Los dos subieron al remoto (la nave nodriza), y Alex ya hizo pull. El capitán pregunta:
¿está a salvo la contraseña de la esclusa?

La misión termina cuando hayas leído la historia, hayas buscado `keys.txt` en el commit más
reciente y en el anterior, hayas encontrado todos los commits que lo tocaron y hayas dicho qué
contraseña hay que cambiar.
"""
QUESTION = "El capitán va a cambiar la contraseña de la esclusa ahora, y necesita saber cuál se filtró. ¿Qué contraseña hay que cambiar?"
PLACEHOLDER = "la contraseña"

HINTS = [
    "`git show HEAD:keys.txt` lee el archivo en el commit más reciente; `HEAD~1` es el commit anterior.",
    "Para un archivo que ya no está en tu carpeta, pon `--` antes de su nombre: `git log --oneline -- keys.txt`.",
    "Cada línea de la misión, en orden; después responde orion-7:\n\n"
    "    $ git log --oneline\n    $ git show HEAD:keys.txt\n    $ git show HEAD~1:keys.txt\n    $ git log --oneline keys.txt\n    $ git log --oneline -- keys.txt",
]

DEBRIEF = """
Quitar `keys.txt` creó un commit nuevo sin él; el commit anterior sigue guardando el archivo como
estaba. `git show HEAD~1:keys.txt` lo leyó, y `git log -- keys.txt` encontró todos los commits que
lo tocaron. Cuando un secreto está en un commit y hiciste push, ya se filtró: cambia el secreto. La
verdadera solución viene antes del commit, como en Polizón: déjalo fuera del staging area.

Comandos para recordar:

    $ git show HEAD~1:keys.txt            # un archivo como lo guardó el commit anterior a HEAD
    $ git log --oneline -- keys.txt       # todos los commits que tocaron un archivo, aunque ya no exista
"""

STEPS = {
    "log": kit.StepText(text="Lee la historia."),
    "guess": kit.StepText(
        text="Primero, predice.",
        question="`keys.txt` ya no está en tu carpeta ni en el commit más reciente. ¿Alguien que tenga esta historia todavía puede leer la contraseña?",
        options=("Sí", "No"),
        reveal="Sí. Quitar el archivo creó un commit nuevo sin él. El commit anterior no cambió: todavía guarda `keys.txt` como estaba. Míralo.",
    ),
    "head": kit.StepText(text="Busca las llaves en el commit más reciente."),
    "before": kit.StepText(text="Busca en el commit anterior."),
    "try": kit.StepText(text="Lista los commits que tocaron las llaves."),
    "trail": kit.StepText(text="Dile a git que `keys.txt` es un archivo."),
}

LOGGED = "*Remove the keys* arriba; *Add the airlock keys* justo debajo. Los dos están en la nave nodriza y en la estación de Alex: mira los pines."
NOT_LOGGED = "Primero lee la historia: `git log --oneline`."
NOT_IN_HEAD = "Claro, era lo esperado: `HEAD` es el commit más reciente, los archivos de hoy, y no tiene `keys.txt`. Esa parte de la solución funcionó."
NOT_HEAD = "Busca `keys.txt` en el commit más reciente: `git show HEAD:keys.txt`."
FOUND = (
    "`HEAD~1` es un commit antes de `HEAD`: aquí, *Add the airlock keys*. Ahí está la contraseña, exactamente como se guardó en el commit.\n\n"
    "La nave nodriza tiene este commit, y Alex también: mira los pines. Quien clone el proyecto después también lo recibe, y puede escribir la misma línea."
)
NOT_FOUND = "Busca en el commit anterior al más reciente: `git show HEAD~1:keys.txt`."
DASHES = "Un archivo que ya no está en tu carpeta necesita `--` antes de su nombre, como dice la última línea de git."
NOT_TRIED = "Lista los commits que tocaron las llaves: `git log --oneline keys.txt`."
TRAIL = (
    "Dos commits tocaron `keys.txt`: el que lo agregó y el que lo quitó.\n\n"
    "Así que un commit posterior no puede borrar lo que guardó un commit anterior. La contraseña llegó a la nave nodriza: "
    "trátala como filtrada, y cámbiala. Reescribir la historia puede ocultarla de las copias futuras, pero no de quien ya "
    "hizo pull, así que igual cambias la contraseña. Por eso, en Polizón, las llaves nunca entraron en un commit.\n\n"
    "Ahora respóndele al capitán en el cuadro de respuesta: ¿qué contraseña se filtró?"
)
NOT_TRAIL = "Pon `--` antes del nombre del archivo: `git log --oneline -- keys.txt`."
RIGHT = "Correcto: se filtró `orion-7`. El capitán la cambia ahora, y la vieja ya no abre nada."
WRONG = "Eso no es lo que tenía `keys.txt`. Léelo de nuevo con `git show HEAD~1:keys.txt`."
TOO_FAR = "Dos commits atrás es antes de que se agregaran las llaves: ese commit no tiene `keys.txt`. Prueba uno atrás."
