"""The command line: parse arguments, call `firstcommit.game` or the web server, print the result."""


def main(argv: list[str] | None = None) -> int:
    """
    Run the command line.

    Parameters
    ----------
    argv : list[str] | None
        Arguments after the program name, or None for ``sys.argv``.

    Returns
    -------
    int
        Exit status.
    """
    raise NotImplementedError
