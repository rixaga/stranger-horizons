"""Exception types with messages meant for the person running the tool."""


class ShError(Exception):
    """Base class for expected, user-facing pipeline errors."""


class ToolMissing(ShError):
    """An external program (FFmpeg, Blender) is not installed or not found."""


class CommandFailed(ShError):
    """An external program ran and failed."""
