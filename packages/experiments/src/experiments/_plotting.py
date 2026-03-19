"""Shared matplotlib style and figure saving utilities."""

from __future__ import annotations

import functools
import io
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec

import matplotlib
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator
from rich.console import Console

matplotlib.rcParams["font.family"] = "serif"
matplotlib.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]
matplotlib.rcParams["mathtext.fontset"] = "stix"

P = ParamSpec("P")

_DOCS_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "docs"
DOCS_IMG_DIR = str(_DOCS_ROOT / "static" / "img" / "results")

console = Console()


def configure_axes(ax: Axes) -> None:
    """Apply shared tick style to an axis.

    Parameters
    ----------
    ax : Axes
        Matplotlib axes to configure.
    """
    if ax.get_xscale() == "linear":
        ax.xaxis.set_minor_locator(AutoMinorLocator())
    if ax.get_yscale() == "linear":
        ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(which="minor", length=3, color="gray", direction="in")
    ax.tick_params(which="major", length=6, direction="in")
    ax.tick_params(top=True, right=True, which="both")


def _savefig(fig: Figure, path_or_buf: Path | io.BytesIO, fmt: str | None = None) -> None:
    """Call savefig with standard defaults.

    Parameters
    ----------
    fig : Figure
        Matplotlib figure.
    path_or_buf : Path | io.BytesIO
        Output path or buffer.
    fmt : str | None
        Format string (e.g. "pdf", "png"). Inferred from path if None.
    """
    fig.savefig(
        path_or_buf,
        format=fmt,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )


def save_figure(fig: Figure, path: Path) -> bool:
    """Save a figure, only writing if content changed.

    Parameters
    ----------
    fig : Figure
        Matplotlib figure.
    path : Path
        Output path.

    Returns
    -------
    bool
        True if file was written.
    """
    if path.exists():
        buf = io.BytesIO()
        fmt = path.suffix.lstrip(".")
        _savefig(fig, buf, fmt=fmt)
        buf.seek(0)
        new_bytes = buf.read()
        existing_bytes = path.read_bytes()
        if new_bytes == existing_bytes:
            return False

    path.parent.mkdir(parents=True, exist_ok=True)
    _savefig(fig, path)
    return True


def docs_figure(filename: str) -> Callable[[Callable[P, Figure]], Callable[P, Figure]]:
    """Save the returned Figure as PNG (for docs) and PDF (for pre-print).

    The decorated function must return a ``matplotlib.figure.Figure``.
    The decorator handles saving, change detection, console output,
    and closing the figure.

    Parameters
    ----------
    filename : str
        Base filename without extension (e.g. "calibration").
    """

    def decorator(func: Callable[P, Figure]) -> Callable[P, Figure]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Figure:
            fig = func(*args, **kwargs)
            stem = Path(filename).stem
            for ext in ("png", "pdf"):
                path = Path(DOCS_IMG_DIR) / f"{stem}.{ext}"
                if save_figure(fig, path):
                    console.print(f"  Saved [blue]{path}[/blue]")
                else:
                    console.print(f"  Unchanged [dim]{path}[/dim]")
            plt.close(fig)
            return fig

        return wrapper

    return decorator
