#!/usr/bin/env python3

import threading
import time
from collections import deque

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import attest_loop


console = Console()

HISTORY_SIZE = 5
INTERVAL     = attest_loop.ATTESTATION_INTERVAL


class AttestationTUI:
    def __init__(self, pubkey, tee_allow, ta_allow):
        self.pubkey    = pubkey
        self.tee_allow = tee_allow
        self.ta_allow  = ta_allow

        self.history     = deque(maxlen=HISTORY_SIZE)
        self.last_result = None

        self.next_attestation = time.monotonic()
        self.running  = True
        self.busy     = False
        self.show_trace = False        # toggled by 'd'

        self.lock = threading.Lock()

    def run_attestation(self, tamper=False):
        if self.busy:
            return

        self.busy = True

        try:
            result = attest_loop.attest_once(
                self.pubkey,
                self.tee_allow,
                self.ta_allow,
                tamper=tamper,
            )

            with self.lock:
                self.last_result = result
                self.history.appendleft(result)

        finally:
            self.busy = False
            self.next_attestation = time.monotonic() + INTERVAL

    # ------------------------------------------------------------------
    # Panels
    # ------------------------------------------------------------------

    def last_result_panel(self):
        with self.lock:
            result = self.last_result

        if result is None:
            return Panel("No attestation has been performed yet.",
                         title="Last Attestation")

        status = "PASS" if result.passed else "FAIL"
        border = "green" if result.passed else "red"

        table = Table(show_header=False, box=None)
        table.add_row("Status",    f"[bold]{status}[/bold]")
        table.add_row("Timestamp", result.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Nonce",     result.nonce)
        table.add_row("Reason",    result.reason)

        return Panel(table, title="Last Attestation", border_style=border)

    def trace_panel(self):
        """
        Execution Trace panel — shows the strace-derived TEE call chain.
        Only rendered when self.show_trace is True.
        """

        with self.lock:
            result = self.last_result

        if result is None or result.trace is None:
            return Panel("No trace available yet.", title="Execution Trace",
                         border_style="dim")

        t = result.trace

        def tick(ok: bool) -> str:
            return "[green]✓[/green]" if ok else "[red]✗[/red]"

        def hi(val: str) -> str:
            return f"[bold cyan]{val}[/bold cyan]"

        rows = [
            ("TEE Driver",
             f"{tick(t.tee_driver_opened)}  /dev/tee0 opened"),

            ("OP-TEE caps",
             f"{tick(bool(t.optee_caps))}  {hi(t.optee_caps) if t.optee_caps else 'not captured'}"),

            ("Session open",
             f"{tick(bool(t.session_uuid))}  TA {hi(t.session_uuid)}  "
             f"origin={hi(t.session_ret)}"),

            ("Nonce SHM",
             f"{tick(bool(t.nonce_shm_size))}  {hi(t.nonce_shm_size)} bytes "
             f"registered as MEMREF_INPUT"),

            ("TA Invoke",
             f"{tick(t.invoke_origin == 'TEEC_ORIGIN_TRUSTED_APP')}  "
             f"ret={hi(t.invoke_ret)}  "
             f"origin={hi(t.invoke_origin)}  "
             f"out={hi(t.invoke_out_size)} bytes"),

            ("Session close",
             f"{tick(t.session_closed)}  TEE_IOC_CLOSE_SESSION"),

            ("Verify",
             f"{tick(result.passed)}  RSA-3072 PSS · TEE hash · TA hash · nonce"),
        ]

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold dim", no_wrap=True)
        table.add_column()

        for label, value in rows:
            table.add_row(label, value)

        border = "green" if result.passed else "red"
        return Panel(table, title="Execution Trace", border_style=border)

    def raw_trace_panel(self):
        """Raw strace text — shown below the parsed trace when 'd' is active."""

        with self.lock:
            result = self.last_result

        if result is None or result.trace is None or not result.trace.raw:
            return None

        # Trim to last 20 lines so it doesn't swamp the screen.
        lines = result.trace.raw.strip().splitlines()
        visible = "\n".join(lines[-20:])

        return Panel(
            f"[dim]{visible}[/dim]",
            title="Raw strace (last 20 lines)",
            border_style="dim",
        )

    def history_table(self):
        table = Table(title="Recent Attestations", expand=True)
        table.add_column("Time")
        table.add_column("Status")
        table.add_column("Reason")
        table.add_column("Nonce")

        with self.lock:
            entries = list(self.history)

        for result in entries:
            status     = "PASS" if result.passed else "FAIL"
            color      = "green" if result.passed else "red"
            has_trace  = "📡" if result.trace else ""

            table.add_row(
                result.timestamp.strftime("%H:%M:%S"),
                f"[{color}]{status}[/{color}]",
                result.reason,
                result.nonce[:16] + "...",
            )

        if not entries:
            table.add_row("-", "-", "No attestations yet", "-")

        return table

    def countdown_panel(self):
        if self.busy:
            text = "[yellow]Attestation in progress...[/yellow]"
        else:
            remaining      = max(0, int(self.next_attestation - time.monotonic()))
            minutes, secs  = divmod(remaining, 60)
            text           = (
                f"[bold]{minutes:02d}:{secs:02d}[/bold]\n"
                "until next automatic attestation"
            )

        return Panel(text, title="Next Attestation", expand=True)

    def render(self):
        header = Panel(
            "[bold]STM32MP1 Remote Attestation[/bold]\n"
            "TrustZone / OP-TEE verification demo",
            title="CAPSTONE",
        )

        trace_hint = " [bold]d[/bold]  hide trace" if self.show_trace \
                     else " [bold]d[/bold]  show trace"

        controls = Panel(
            "[bold]t[/bold]  tamper test    "
            "[bold]q[/bold]  quit    "
            "[bold]auto[/bold]  every 120 seconds   "
            + trace_hint,
            title="Controls",
        )

        parts = [
            header,
            self.last_result_panel(),
        ]

        if self.show_trace:
            parts.append(self.trace_panel())
            raw = self.raw_trace_panel()
            if raw:
                parts.append(raw)

        parts.append(self.history_table())
        parts.append(self.countdown_panel())
        parts.append(controls)

        return Group(*parts)


# ---------------------------------------------------------------------------
# Keyboard loop (Windows)
# ---------------------------------------------------------------------------

def keyboard_loop(app):
    import msvcrt

    while app.running:
        if msvcrt.kbhit():
            key = msvcrt.getwch().lower()

            if key == "q":
                app.running = False
                break

            if key == "t":
                threading.Thread(
                    target=app.run_attestation,
                    kwargs={"tamper": True},
                    daemon=True,
                ).start()

            if key == "d":
                app.show_trace = not app.show_trace

        time.sleep(0.05)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    console.clear()
    console.print("Loading attestation verifier...")

    pubkey, tee_allow, ta_allow = attest_loop.load_verifier()

    app = AttestationTUI(pubkey, tee_allow, ta_allow)

    # Immediate first attestation.
    app.run_attestation()

    keyboard_thread = threading.Thread(
        target=keyboard_loop, args=(app,), daemon=True
    )
    keyboard_thread.start()

    try:
        with Live(
            app.render(),
            console=console,
            refresh_per_second=4,
            screen=True,
        ) as live:

            while app.running:
                if (not app.busy
                        and time.monotonic() >= app.next_attestation):
                    threading.Thread(
                        target=app.run_attestation, daemon=True
                    ).start()

                live.update(app.render())
                time.sleep(0.25)

    except KeyboardInterrupt:
        app.running = False

    console.clear()
    console.print("Attestation demo stopped.")


if __name__ == "__main__":
    main()