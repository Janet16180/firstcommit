# Spanish glossary

The game's Spanish is neutral Latin American Spanish, written as a Latin American teacher would
explain Git to a beginner. Git and programming terms stay in English, as Latin American
developers say them; general words are translated. Commands, file names, branch names, commit
messages and git's own output never change.

`tests/test_translations.py` keeps the rules below that a test can keep: its `NEVER` list holds
the forms that must not appear in any Spanish text.

## Git terms kept in English

| English | Spanish form | Grammar and examples |
|---|---|---|
| commit (noun) | el commit, los commits | "un commit nuevo", "el último commit" |
| commit (verb) | hacer un commit, hacer commit de | "haz un commit", "hiciste commit de `map.txt`" |
| push | el push; hacer push | "haz push", "tu push fue rechazado", "hacer push de `main`" |
| pull | el pull; hacer pull | "haz pull", "`git pull` trae el commit" |
| fetch | el fetch; hacer fetch | "haz fetch", "desde el último fetch" |
| merge | el merge; hacer merge | "un merge", "haz merge de la branch" |
| rebase | el rebase; hacer rebase | "con un rebase" |
| stash | el stash | "guarda el cambio en el stash" |
| clone | el clone; clonar | "un clone tiene toda la historia", "clona el repositorio" (the verb is the one Latin American developers use) |
| reset | el reset; hacer reset | |
| revert | el revert; hacer revert | |
| log | el log | "el log de `oxygen.cfg`" |
| diff | el diff | "el diff muestra..." |
| branch | el branch, los branches | "el branch `main`", "un branch nuevo" (masculine, as developers say it) |
| staging area | el staging area | "en el staging area", "sacar del staging area" |
| stage (verb) | agregar al staging area | "agrega `map.txt` al staging area"; "está en el staging area" for staged |
| unstage (verb) | sacar del staging area | |
| upstream | el upstream | "`origin/main` es su upstream" |
| hash | el hash, los hashes | |
| HEAD | HEAD | no article: "HEAD apunta a `main`" |
| main | main | always as code: `main` |
| remote-tracking branch | `origin/main` | named by the code span, not translated |

## General words, translated

| English | Spanish |
|---|---|
| repository | el repositorio |
| folder | la carpeta |
| working folder | la carpeta de trabajo (not directorio de trabajo) |
| file | el archivo |
| remote | el remoto |
| untracked | sin seguimiento ("lo lista como sin seguimiento") |
| snapshot | la instantánea |
| history | la historia (not historial) |
| author | el autor, la autora; "quién lo hizo" when the person is unknown |
| computer | la computadora |
| terminal | la terminal |
| press (a key) | presiona |
| Tab, Enter | la tecla Tab, Enter |

## The game's world

| English | Spanish |
|---|---|
| capsule | la cápsula |
| workshop (the working folder) | el taller; first mention in a level: "tu carpeta de trabajo (el taller)" |
| cargo dock (the staging area) | el muelle de carga; first mention in a level: "el staging area (el muelle de carga)" |
| vault | la bóveda; first mention in a level: "tu repositorio (la bóveda)" |
| mothership | la nave nodriza; first mention in a level: "el remoto (la nave nodriza)" |
| (loading) dock | el muelle de carga |
| base | la base |
| crew | la tripulación |
| night shift | el turno de noche |
| mission | la misión |
| flight recorder | el registro de vuelo |
| black box | la caja negra |
| airlock | la esclusa |
| the chain (the picture of commits) | la cadena |
| name tag (a branch, as the chain draws it) | la etiqueta |
| bookmark (`origin/main`) | el marcador |
| the move log (`git reflog`) | el log de movimientos |

## Style

- Address the player as `tú`, and a group as `ustedes`; never `vosotros`.
- Use the simple past for what just happened, not the present perfect: "Le preguntaste a Git, así
  que se negó", not "Le has preguntado a Git, así que se ha negado". "Git creó la carpeta", not
  "Git ha creado".
- Latin American words: computadora (not ordenador), presiona (not pulsa), agregar (not añadir),
  archivo.
- Keep the English text's shape: the same code spans, placeholders, paragraphs and bullets.
- Alex is "Alex" with they/them in English; in Spanish, name Alex or write around the pronoun
  ("el commit de Alex", "su línea"), with no gendered adjective for Alex.
