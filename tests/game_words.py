import re

GAME_WORDS: dict[str, dict[str, tuple[str, str]]] = {
    "en": {
        "workshop": (r"\bworkshop\b", r"working\s+folder\s+\(the\s+workshop\)"),
        "cargo dock": (r"\bcargo\s+dock\b", r"staging\s+area\s+\(the\s+cargo\s+dock\)"),
        "vault": (r"\bvault\b", r"repository\s+\(the\s+vault\)"),
        "mothership": (r"\bmothership\b", r"remote\s+\(the\s+mothership\)"),
    },
    "es": {
        "workshop": (r"\btaller\b", r"carpeta\s+de\s+trabajo\s+\(el\s+taller\)"),
        "cargo dock": (r"\bmuelle\s+de\s+carga\b", r"staging\s+area\s+\(el\s+muelle\s+de\s+carga\)"),
        "vault": (r"\bbóveda\b", r"repositorio\s+\(la\s+bóveda\)"),
        "mothership": (r"\bnave\s+nodriza\b", r"remoto\s+\(la\s+nave\s+nodriza\)"),
    },
}
"""Each game word, by language: how to find it, and the pairing with what it really is that a level's texts must hold once."""


def unpaired(text: str, language: str) -> list[str]:
    """
    Name the game words a text uses without saying, even once, what they really are.

    Parameters
    ----------
    text : str
        Every text one level, deck or message holds, in one language.
    language : str
        ``"en"`` or ``"es"``.

    Returns
    -------
    list[str]
        The game words (by their English name) used and never paired, such as ``"vault"``.
    """
    return [word for word, (used, paired) in GAME_WORDS[language].items() if re.search(used, text, re.IGNORECASE) and not re.search(paired, text, re.IGNORECASE)]
