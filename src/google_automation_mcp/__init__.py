"""
Google Automation MCP Server

MCP server for Google Apps Script and Google Workspace automation.
Supports 50 tools across Gmail, Drive, Sheets, Calendar, Docs, and Apps Script.
"""

__version__ = "0.5.0"

# Cache for lazy-loaded modules to avoid recursion
_lazy_cache = {}


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "appscript_tools":
        if name not in _lazy_cache:
            import importlib
            _lazy_cache[name] = importlib.import_module(
                ".appscript_tools", __name__
            )
        return _lazy_cache[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
