from __future__ import annotations

import re

from .schemas import StackFrame


_PYTHON_FRAME = re.compile(
    r'File ["\'](?P<file>[^"\']+)["\'],\s*'
    r"line\s*(?P<line>\d+)"
    r'(?:,\s*in\s*(?P<function>[\w.<>$-]+))?'
)


_GENERIC_FRAME = re.compile(
    r"(?P<file>"
    r"(?:[A-Za-z]:[\\/]|/|\.\.?[\\/])?"
    r"[^\s():]+"
    r"\.(?:py|js|jsx|ts|tsx)"
    r")"
    r":(?P<line>\d+)"
    r"(?::(?P<column>\d+))?"
)


def parse_stack_trace(
    stack_trace: str | None,
) -> list[StackFrame]:

    if not stack_trace:
        return []

    frames: list[StackFrame] = []

    seen: set[
        tuple[
            str | None,
            int | None,
            int | None,
            str | None,
        ]
    ] = set()

    for line in stack_trace.splitlines():

        frame = _parse_line(line)

        if (
            frame is None
            or frame.line_number is None
        ):
            continue

        key = (
            frame.file_path,
            frame.line_number,
            frame.column_number,
            frame.function_name,
        )

        if key in seen:
            continue

        seen.add(key)
        frames.append(frame)

    return frames


def _parse_line(
    line: str,
) -> StackFrame | None:

    match = _PYTHON_FRAME.search(
        line
    )

    if match:

        return StackFrame(
            file_path=match.group(
                "file"
            ),
            function_name=match.group(
                "function"
            ),
            line_number=int(
                match.group("line")
            ),
        )

    node_result = _parse_node_line(
        line
    )

    if node_result:
        return node_result

    match = _GENERIC_FRAME.search(
        line
    )

    if match:

        return StackFrame(
            file_path=match.group(
                "file"
            ),
            line_number=int(
                match.group("line")
            ),
            column_number=(
                int(
                    match.group("column")
                )
                if match.group("column")
                else None
            ),
        )

    return None


def _parse_node_line(
    line: str,
) -> StackFrame | None:

    value = line.strip()

    if not value.startswith("at "):
        return None

    value = value[3:].strip()

    function_name: str | None = None

    if (
        value.endswith(")")
        and "(" in value
    ):

        function_name, value = value.split(
            "(",
            1,
        )

        function_name = (
            function_name.strip()
            or None
        )

        value = value[:-1]

    parts = value.rsplit(
        ":",
        2,
    )

    if (
        len(parts) == 3
        and parts[1].isdigit()
        and parts[2].isdigit()
    ):

        return StackFrame(
            file_path=parts[0],
            function_name=function_name,
            line_number=int(parts[1]),
            column_number=int(parts[2]),
        )

    if (
        len(parts) == 2
        and parts[1].isdigit()
    ):

        return StackFrame(
            file_path=parts[0],
            function_name=function_name,
            line_number=int(parts[1]),
        )

    return None