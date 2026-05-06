"""
AUV Control TUI
===============

A Textual TUI for monitoring and controlling an Autonomous Underwater Vehicle.

Layout:
    ╭───────────────╮ ╭─────────────────────╮
    │  Services     │ │  Telemetry          │
    ├───────────────┤ │  IMU / Depth / Pwr  │
    │  Controllers  │ ├─────────────────────┤
    │               │ │  Manual Command     │
    ╰───────────────╯ ╰─────────────────────╯
              [ footer: keybindings · DB status ]

External interfaces are imported from the auvsoftware package; if unavailable
the app falls back to inert stubs so the UI can still be exercised standalone.
Every external call is clearly labelled and isolated to keep this file focused
on presentation logic only.

Run with:  python ui.py
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Static,
)

# ─────────────────────────────────────────────────────────────────────────────
# External interface imports (with inert fallback stubs)
# ─────────────────────────────────────────────────────────────────────────────
# Each external call site below is clearly labelled `# EXTERNAL:` so business
# logic stays out of this file. If the real packages aren't importable we fall
# back to no-op stubs so the UI still runs for design review.

try:
    from auvsoftware.process_manager import ProcessManager  # type: ignore
except ImportError:  # pragma: no cover - stub for standalone preview
    class ProcessManager:  # type: ignore[no-redef]
        """Stub — replace with auvsoftware.process_manager.ProcessManager."""
        def start(self, name: str) -> None: ...
        def stop(self, name: str) -> None: ...
        def start_all(self) -> None: ...
        def stop_all(self) -> None: ...
        def status(self) -> dict[str, dict]:
            return {
                "db": {"running": False, "pid": None},
                "hardware_interface": {"running": False, "pid": None},
            }

try:
    from auvsoftware.hardware_interface.process_manager import (  # type: ignore
        HardwareProcessManager,
    )
except ImportError:  # pragma: no cover
    class HardwareProcessManager:  # type: ignore[no-redef]
        """Stub — replace with auvsoftware.hardware_interface.process_manager."""
        def start(self, name: str) -> None: ...
        def stop(self, name: str) -> None: ...
        def status(self) -> dict[str, dict]:
            return {
                name: {"enabled": False, "detected": False,
                       "running": False, "pid": None}
                for name in CONTROLLERS
            }

try:
    from auvsoftware.quick_request import AUVClient  # type: ignore
except ImportError:  # pragma: no cover
    class AUVClient:  # type: ignore[no-redef]
        """Stub — replace with auvsoftware.quick_request.AUVClient."""
        def latest(self, table: str) -> dict | None: return None
        def post(self, table: str, **fields: Any) -> None: ...


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
SERVICES: tuple[str, ...] = ("db", "hardware_interface")
CONTROLLERS: tuple[str, ...] = (
    "esc", "arm", "imu", "psa", "torpedo", "pressure", "display",
)
INPUT_FIELDS: tuple[str, ...] = (
    "SURGE", "SWAY", "HEAVE", "ROLL", "PITCH", "YAW", "S1", "S2", "S3", "ARM",
)
TELEMETRY_TABLES: tuple[str, ...] = ("imu", "depth", "power_safety")

POLL_INTERVAL: float = 0.5   # seconds — telemetry poll cadence
STALE_AFTER: float  = 2.0   # seconds — mark series stale after this gap
HISTORY: int        = 60    # samples kept per channel


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TelemetrySeries:
    """Ring buffer of recent samples for a single channel + last-seen ts."""
    samples: Deque[float] = field(default_factory=lambda: deque(maxlen=HISTORY))
    last_update: float = 0.0

    def push(self, v: float | None) -> None:
        if v is None:
            return
        try:
            self.samples.append(float(v))
            self.last_update = time.monotonic()
        except (TypeError, ValueError):
            pass

    def is_stale(self, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        return self.last_update == 0.0 or (now - self.last_update) > STALE_AFTER

    def latest(self) -> float | None:
        return self.samples[-1] if self.samples else None


# ─────────────────────────────────────────────────────────────────────────────
# Panel widgets
# ─────────────────────────────────────────────────────────────────────────────
class PanelTitle(Static):
    """Small caps section title rendered above each panel body."""


class ServicesPanel(Vertical):
    """Top-left — ProcessManager.status() + per-service start/stop toggles.

    Reactive `service_state` is updated externally by the App's refresh tick;
    `watch_service_state` repaints the table.
    """

    DEFAULT_CSS = """
    ServicesPanel { height: 1fr; }
    ServicesPanel .row {
        height: 3; padding: 0 1; layout: horizontal;
        border-bottom: dashed $surface-lighten-2;
    }
    ServicesPanel .row.last { border-bottom: none; }
    ServicesPanel .name { width: 1fr; content-align: left middle; }
    ServicesPanel .pid  { width: 12;  content-align: left middle; color: $text-muted; }
    ServicesPanel .dot  { width: 3;   content-align: center middle; }
    ServicesPanel Button { min-width: 9; height: 1; margin-left: 1; }
    ServicesPanel .running  { color: $success; }
    ServicesPanel .stopped  { color: $error; }
    """

    service_state: reactive[dict[str, dict]] = reactive(dict, recompose=False)

    def compose(self) -> ComposeResult:
        yield PanelTitle("◆  SERVICES")
        for i, name in enumerate(SERVICES):
            classes = "row" + (" last" if i == len(SERVICES) - 1 else "")
            with Horizontal(classes=classes, id=f"svc-row-{name}"):
                yield Static("●", classes="dot stopped", id=f"svc-dot-{name}")
                yield Static(name, classes="name")
                yield Static("pid —", classes="pid", id=f"svc-pid-{name}")
                yield Button("start", id=f"svc-toggle-{name}",
                             variant="success")
        yield Static("[1] db   [2] hardware_interface   [a] start all   [A] stop all",
                     classes="hint")

    def watch_service_state(self, state: dict[str, dict]) -> None:
        for name in SERVICES:
            info = state.get(name, {"running": False, "pid": None})
            running = bool(info.get("running"))
            pid = info.get("pid")
            dot = self.query_one(f"#svc-dot-{name}", Static)
            dot.update("●")
            dot.set_class(running, "running")
            dot.set_class(not running, "stopped")
            self.query_one(f"#svc-pid-{name}", Static).update(
                f"pid {pid}" if pid else "pid —"
            )
            btn = self.query_one(f"#svc-toggle-{name}", Button)
            btn.label = "stop" if running else "start"
            btn.variant = "error" if running else "success"


class ControllersPanel(VerticalScroll):
    """Bottom-left — HardwareProcessManager.status() per controller with start/stop.

    Three dot states per row:
        not enabled                 → grey  (●)
        enabled, not detected       → amber (◐)
        enabled, detected, running  → green (●)
    """

    DEFAULT_CSS = """
    ControllersPanel { height: 1fr; }
    ControllersPanel .row {
        height: 3; padding: 0 1; layout: horizontal;
        border-bottom: dashed $surface-lighten-2;
    }
    ControllersPanel .row.last { border-bottom: none; }
    ControllersPanel .dot  { width: 3;  content-align: center middle; }
    ControllersPanel .name { width: 10; content-align: left middle; }
    ControllersPanel .flag {
        width: 12; content-align: left middle; color: $text-muted;
    }
    ControllersPanel Button { min-width: 9; height: 1; margin-left: 1; }
    ControllersPanel .dot-on      { color: $success; }
    ControllersPanel .dot-partial { color: $warning; }
    ControllersPanel .dot-off     { color: $text-muted; }
    """

    controller_state: reactive[dict[str, dict]] = reactive(dict, recompose=False)

    def compose(self) -> ComposeResult:
        yield PanelTitle("◆  CONTROLLERS")
        for i, name in enumerate(CONTROLLERS):
            row_cls = "row" + (" last" if i == len(CONTROLLERS) - 1 else "")
            with Horizontal(classes=row_cls):
                yield Static("●", classes="dot dot-off", id=f"ctrl-dot-{name}")
                yield Static(name, classes="name")
                yield Static("en:— det:—", classes="flag", id=f"ctrl-flag-{name}")
                yield Button("start", id=f"ctrl-toggle-{name}", variant="success")

    def watch_controller_state(self, state: dict[str, dict]) -> None:
        for name in CONTROLLERS:
            info     = state.get(name, {})
            enabled  = bool(info.get("enabled"))
            detected = bool(info.get("detected"))
            running  = bool(info.get("running"))

            dot = self.query_one(f"#ctrl-dot-{name}", Static)
            if running:
                dot.update("●")
                dot.set_classes("dot dot-on")
            elif enabled and not detected:
                dot.update("◐")
                dot.set_classes("dot dot-partial")
            else:
                dot.update("●")
                dot.set_classes("dot dot-off")

            self.query_one(f"#ctrl-flag-{name}", Static).update(
                f"en:{'y' if enabled else 'n'} det:{'y' if detected else 'n'}"
            )
            btn = self.query_one(f"#ctrl-toggle-{name}", Button)
            btn.label   = "stop"  if running else "start"
            btn.variant = "error" if running else "success"


class TimeSeriesPlot(Static):
    """A single plotext line-graph widget for one group of channels."""

    DEFAULT_CSS = """
    TimeSeriesPlot { height: 6; margin: 0 0 0 0; }
    """

    def __init__(
        self,
        title: str,
        channels: list[tuple[str, str]],
        unit: str = "",
    ) -> None:
        super().__init__()
        self._title    = title
        self._channels = channels   # [(key, label), ...]
        self._unit     = unit
        self._data: dict[str, list[float]] = {k: [] for k, _ in channels}

    def update_series(self, key: str, samples: list[float]) -> None:
        if key in self._data:
            self._data[key] = samples

    def redraw(self) -> None:
        import plotext as plt
        from rich.text import Text

        w = max(self.size.width - 2, 20)
        h = max(self.size.height - 2, 4)

        plt.clf()
        plt.theme("dark")
        plt.plotsize(w, h)

        has_data = False
        all_values: list[float] = []
        value_labels: list[str] = []

        for key, label in self._channels:
            data = self._data[key]
            if data:
                has_data = True
                all_values.extend(data)
                plt.plot(data, marker="braille")
                value_labels.append(f"{label}: {data[-1]:+.3f}")

        # Title carries the group name and each channel's latest value.
        suffix = "    " + "  ".join(value_labels) if value_labels else ""
        plt.title(self._title + suffix)

        # Y-axis: only min and max ticks.
        if all_values:
            lo, hi = min(all_values), max(all_values)
            if abs(hi - lo) > 1e-9:
                plt.yticks([lo, hi], [f"{lo:.2f}", f"{hi:.2f}"])

        # Strip x-axis ticks and label entirely.
        plt.xfrequency(0)

        if has_data:
            self.update(Text.from_ansi(plt.build()))
        else:
            self.update(f"  [dim]{self._title} — waiting for data[/dim]")


class TelemetryPanel(VerticalScroll):
    """Top-right — scrollable pane of grouped time-series plots."""

    DEFAULT_CSS = """
    TelemetryPanel { height: 1fr; }
    """

    # Groups: (title, [(key, label), ...], y-axis unit)
    PLOTS: tuple[tuple[str, list[tuple[str, str]], str], ...] = (
        ("Accelerometer", [("imu.ax", "x"), ("imu.ay", "y"), ("imu.az", "z")], "m/s²"),
        ("Gyroscope",     [("imu.gx", "x"), ("imu.gy", "y"), ("imu.gz", "z")], "rad/s"),
        ("Magnetometer",  [("imu.mx", "x"), ("imu.my", "y"), ("imu.mz", "z")], "µT"),
        ("Depth",         [("depth.m", "depth")], "m"),
        ("Power",         [("psa.v", "V"), ("psa.i", "A"), ("psa.t", "°C")], ""),
    )

    # Flat list of all channel keys — used by App to initialise _telemetry.
    ALL_KEYS: tuple[str, ...] = tuple(
        key
        for _, channels, _ in PLOTS
        for key, _ in channels
    )

    telemetry: reactive[dict[str, TelemetrySeries]] = reactive(
        dict, recompose=False, always_update=True
    )

    def compose(self) -> ComposeResult:
        yield PanelTitle("◆  TELEMETRY")
        for title, channels, unit in self.PLOTS:
            yield TimeSeriesPlot(title=title, channels=channels, unit=unit)

    def watch_telemetry(self, telemetry: dict[str, TelemetrySeries]) -> None:
        for plot in self.query(TimeSeriesPlot):
            for key, _ in plot._channels:
                series = telemetry.get(key)
                if series:
                    plot.update_series(key, list(series.samples))
            plot.redraw()


class ManualCommandPanel(Vertical):
    """Bottom-right — composes an `inputs` row and POSTs it.

    No business logic lives here: the Send button hands the dict off to the
    App, which calls AUVClient.post("inputs", **fields) — the single labelled
    external call.
    """

    DEFAULT_CSS = """
    ManualCommandPanel { height: 1fr; }
    ManualCommandPanel .grid {
        layout: grid; grid-size: 4 3; grid-gutter: 1;
        padding: 1; height: auto;
    }
    ManualCommandPanel .field { layout: vertical; height: 4; }
    ManualCommandPanel .field Label { color: $text-muted; }
    ManualCommandPanel Input { height: 3; }
    ManualCommandPanel .actions {
        layout: horizontal; padding: 1; height: 5;
    }
    ManualCommandPanel .actions Button { margin-right: 1; }
    ManualCommandPanel .ack { color: $success; padding: 0 1; height: 1; }
    """

    last_ack: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield PanelTitle("◆  MANUAL COMMAND  ›  inputs")
        with Vertical(classes="grid"):
            for name in INPUT_FIELDS:
                with Vertical(classes="field"):
                    yield Label(name)
                    yield Input(placeholder="0", id=f"cmd-{name}",
                                value="0", type="number")
        with Horizontal(classes="actions"):
            yield Button("Send", id="cmd-send", variant="primary")
            yield Button("Zero all", id="cmd-zero")
            yield Static("", id="cmd-ack", classes="ack")

    def collect(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for name in INPUT_FIELDS:
            raw = self.query_one(f"#cmd-{name}", Input).value.strip()
            try:
                out[name] = float(raw) if raw else 0.0
            except ValueError:
                out[name] = 0.0
        return out

    def zero(self) -> None:
        for name in INPUT_FIELDS:
            self.query_one(f"#cmd-{name}", Input).value = "0"

    def watch_last_ack(self, ack: str) -> None:
        self.query_one("#cmd-ack", Static).update(ack)


# ─────────────────────────────────────────────────────────────────────────────
# Footer status bar
# ─────────────────────────────────────────────────────────────────────────────
class StatusBar(Static):
    """Single-line bar above the keybinding footer; shows DB reachability."""

    DEFAULT_CSS = """
    StatusBar { dock: bottom; height: 1; padding: 0 1;
                background: $boost; color: $text; }
    StatusBar.online  { background: $success-darken-2; color: $text; }
    StatusBar.offline { background: $error-darken-2;   color: $text; }
    """

    db_online: reactive[bool] = reactive(False)
    last_post: reactive[str] = reactive("")

    def watch_db_online(self, online: bool) -> None:
        self.set_class(online, "online")
        self.set_class(not online, "offline")
        self._refresh_content()

    def watch_last_post(self, _ack: str) -> None:
        self._refresh_content()

    def _refresh_content(self) -> None:
        badge = "● DB ONLINE" if self.db_online else "● DB OFFLINE"
        tail = f"   {self.last_post}" if self.last_post else ""
        self.update(f"{badge}    AUV CONTROL · v0.1{tail}")


# ─────────────────────────────────────────────────────────────────────────────
# Log viewer screen
# ─────────────────────────────────────────────────────────────────────────────
class LogScreen(ModalScreen):
    """Full-screen modal that tails the AUV log file. Press Escape or L to close."""

    BINDINGS = [("escape", "dismiss", "Close"), ("l", "dismiss", "Close")]

    DEFAULT_CSS = """
    LogScreen { align: center middle; }
    LogScreen > Vertical {
        width: 95%; height: 90%;
        border: round $accent;
        background: $panel;
    }
    LogScreen #log-content { padding: 0 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield PanelTitle("◆  PROCESS LOGS  (Esc to close, auto-refreshes every 2s)")
            yield VerticalScroll(Static(id="log-content"), id="log-scroll")

    def on_mount(self) -> None:
        self._refresh_log()
        self.set_interval(2.0, self._refresh_log)

    def _refresh_log(self) -> None:
        from pathlib import Path

        from auvsoftware.config import get_env
        from auvsoftware.logging_config import _PROJECT_ROOT

        log_path = Path(get_env("AUV_LOG_PATH", default="auv.log"))
        if not log_path.is_absolute():
            log_path = _PROJECT_ROOT / log_path
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()
            content = "\n".join(lines[-300:]) or "(no log entries yet)"
        except FileNotFoundError:
            content = f"(log file not found: {log_path})\nStart some processes first."
        self.query_one("#log-content", Static).update(content)
        self.query_one("#log-scroll", VerticalScroll).scroll_end(animate=False)


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────
class AUVControlApp(App):
    """Main app — wires panels together, owns the poll worker, owns the
    external interface instances. All external calls below are tagged
    `# EXTERNAL:` so they're easy to grep.
    """

    CSS = """
    Screen { background: $background; }
    #grid {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 1fr;
        grid-rows: 1fr 1fr;
        grid-gutter: 1;
        padding: 1;
    }
    ServicesPanel, ControllersPanel, TelemetryPanel, ManualCommandPanel {
        border: round $surface-lighten-2;
        background: $panel;
        padding: 0 1;
    }
    PanelTitle {
        color: $accent; text-style: bold;
        padding: 0 1; height: 1;
    }
    .hint { color: $text-muted; padding: 1; }
    """

    BINDINGS = [
        Binding("q", "quit_safely", "Quit"),
        Binding("r", "refresh_all", "Refresh"),
        Binding("l", "show_logs", "Logs"),
        Binding("a", "start_all_services", "Start all"),
        Binding("A", "stop_all_services", "Stop all", show=False),
        Binding("1", "toggle_service('db')", "DB", show=False),
        Binding("2", "toggle_service('hardware_interface')", "HW",
                show=False),
        Binding("z", "zero_inputs", "Zero inputs"),
        Binding("ctrl+s", "send_inputs", "Send"),
    ]

    def __init__(self) -> None:
        super().__init__()
        # External interface instances — single ownership point.
        self.pm = ProcessManager()                # EXTERNAL: owned here
        self.hpm = HardwareProcessManager()       # EXTERNAL: owned here
        self.client = AUVClient()                 # EXTERNAL: owned here
        # Telemetry ring buffers, keyed to TelemetryPanel.ALL_KEYS.
        self._telemetry: dict[str, TelemetrySeries] = {
            key: TelemetrySeries() for key in TelemetryPanel.ALL_KEYS
        }

    # ── compose ──────────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Grid(id="grid"):
            yield ServicesPanel(id="services")
            yield TelemetryPanel(id="telemetry")
            yield ControllersPanel(id="controllers")
            yield ManualCommandPanel(id="manual")
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "AUV Control"
        self.sub_title = "autonomous underwater vehicle · ground station"
        # Initial paint + recurring poll.
        self.action_refresh_all()
        self.set_interval(POLL_INTERVAL, self._poll_telemetry)
        self.set_interval(1.0, self._poll_processes)

    # ── pollers ──────────────────────────────────────────────────────────
    @work(exclusive=True, thread=True, group="telemetry")
    def _poll_telemetry(self) -> None:
        """Runs every POLL_INTERVAL. Pulls latest() for each table; gracefully
        degrades to 'DB offline' on any exception.
        """
        online = True
        for table in TELEMETRY_TABLES:
            try:
                row = self.client.latest(table)            # EXTERNAL: read
            except Exception:
                online = False
                row = None
            if not row:
                continue
            self._ingest_telemetry(table, row)

        # Trigger reactive watchers by re-binding the dict.
        self.query_one(TelemetryPanel).telemetry = dict(self._telemetry)
        status = self.query_one(StatusBar)
        status.db_online = online

    def _ingest_telemetry(self, table: str, row: dict) -> None:
        """Map raw rows from `latest()` onto our channel ring buffers.
        Defensive — missing keys just skip; never raises.
        """
        if table == "imu":
            mapping = {
                "ax": "ACCEL_X", "ay": "ACCEL_Y", "az": "ACCEL_Z",
                "gx": "GYRO_X",  "gy": "GYRO_Y",  "gz": "GYRO_Z",
                "mx": "MAG_X",   "my": "MAG_Y",   "mz": "MAG_Z",
            }
            for short, db_key in mapping.items():
                self._telemetry[f"imu.{short}"].push(row.get(db_key))
        elif table == "depth":
            self._telemetry["depth.m"].push(row.get("DEPTH"))
        elif table == "power_safety":
            self._telemetry["psa.v"].push(row.get("B1_VOLTAGE"))
            self._telemetry["psa.i"].push(row.get("B1_CURRENT"))
            self._telemetry["psa.t"].push(row.get("B1_TEMP"))

    def _poll_processes(self) -> None:
        """Pull both process-manager statuses on a slower cadence."""
        try:
            svc = self.pm.status()                          # EXTERNAL: read
        except Exception:
            svc = {n: {"running": False, "pid": None} for n in SERVICES}
        try:
            ctrl = self.hpm.status()                        # EXTERNAL: read
        except Exception:
            ctrl = {n: {"enabled": False, "detected": False,
                        "running": False, "pid": None} for n in CONTROLLERS}
        self.query_one(ServicesPanel).service_state = svc
        self.query_one(ControllersPanel).controller_state = ctrl

    # ── actions ──────────────────────────────────────────────────────────
    def action_show_logs(self) -> None:
        self.push_screen(LogScreen())

    def action_refresh_all(self) -> None:
        """`r` — force-refresh every panel immediately."""
        self._poll_processes()
        self._poll_telemetry()

    def action_quit_safely(self) -> None:
        """`q` — stop all services then exit."""
        try:
            self.pm.stop_all()                              # EXTERNAL: write
        except Exception:
            pass
        self.exit()

    def action_start_all_services(self) -> None:
        try:
            self.pm.start_all()                             # EXTERNAL: write
        except Exception:
            pass
        self._poll_processes()

    def action_stop_all_services(self) -> None:
        try:
            self.pm.stop_all()                              # EXTERNAL: write
        except Exception:
            pass
        self._poll_processes()

    def action_toggle_service(self, name: str) -> None:
        self._toggle_service(name)

    def action_zero_inputs(self) -> None:
        self.query_one(ManualCommandPanel).zero()

    def action_send_inputs(self) -> None:
        self._send_inputs()

    # ── service start/stop ───────────────────────────────────────────────
    def _toggle_controller(self, name: str) -> None:
        info = self.query_one(ControllersPanel).controller_state.get(name, {})
        try:
            if info.get("running"):
                self.hpm.stop(name)
            else:
                self.hpm.start(name)
        except Exception as exc:
            self.notify(f"{name}: {exc}", severity="error")
        self._poll_processes()

    def _toggle_service(self, name: str) -> None:
        info = self.query_one(ServicesPanel).service_state.get(name, {})
        try:
            if info.get("running"):
                self.pm.stop(name)                          # EXTERNAL: write
            else:
                self.pm.start(name)                         # EXTERNAL: write
        except Exception as exc:
            self.notify(f"{name}: {exc}", severity="error")
        self._poll_processes()

    @on(Button.Pressed)
    def _on_button(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("svc-toggle-"):
            self._toggle_service(bid.removeprefix("svc-toggle-"))
        elif bid.startswith("ctrl-toggle-"):
            self._toggle_controller(bid.removeprefix("ctrl-toggle-"))
        elif bid == "cmd-send":
            self._send_inputs()
        elif bid == "cmd-zero":
            self.query_one(ManualCommandPanel).zero()

    # ── manual command send ──────────────────────────────────────────────
    def _send_inputs(self) -> None:
        panel = self.query_one(ManualCommandPanel)
        fields = panel.collect()
        try:
            self.client.post("inputs", **fields)            # EXTERNAL: write
            panel.last_ack = f"sent · {time.strftime('%H:%M:%S')}"
            self.query_one(StatusBar).last_post = (
                f"last cmd → inputs @ {time.strftime('%H:%M:%S')}"
            )
        except Exception as exc:
            panel.last_ack = f"error: {exc}"
            self.notify(f"send failed: {exc}", severity="error")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    AUVControlApp().run()


if __name__ == "__main__":
    main()
