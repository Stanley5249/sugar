"""Demonstrates how traceback works with sugar."""

import time

from sugar import CommandApp

DIALOG = r"""Amy: "Knock, knock."

Bob: "Who's there?"

Amy: "Interrupting cow."

Bob: "Interrupting cow wh—"

(Try to "Moo!" by pressing `Ctrl + C` or `Command + .` on macOS.)
"""

COWSAY_MOO = r"""
Amy:
 ______
< Moo! >
 ------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
"""

COWSAY_NOTHING = r"""
Amy:
^__^
(oo)\_______
(__)\       )\/\
    ||----w |
    ||     ||
"""


app = CommandApp()


@app.command("cow", "moo")
def interrupting_cow(t: float) -> None:
    """Interrupting cow says moo.

    Try to raise a KeyboardInterrupt to make the cow say "Moo!".

    To raise a KeyboardInterrupt on different operating systems:
        Windows : `Ctrl + C`
        Linux   : `Ctrl + C`
        macOS   : `Command + .` or `Ctrl + C`

    Note:
        sugar will suppress errors and print them to stderr.

    Args:
        t: The time to wait for the cow to interrupt.
    """
    print(DIALOG)
    try:
        end = time.time() + t
        while True:
            r = end - time.time()
            if r < 0:
                break
            print(f"{r:.0f} ...")
            time.sleep(min(r, 1))
    except KeyboardInterrupt:
        print(COWSAY_MOO)
        raise
    else:
        print(COWSAY_NOTHING)


if __name__ == "__main__":
    app.cycle()
