"""Framework adapters for Agent Skills SDK."""

from .base import BaseAdapter

__all__ = ["BaseAdapter"]

try:
    from .langchain import LangChainAdapter

    __all__.append("LangChainAdapter")
except ImportError:
    pass

try:
    from .crewai import CrewAIAdapter

    __all__.append("CrewAIAdapter")
except ImportError:
    pass

try:
    from .agno import AgnoAdapter

    __all__.append("AgnoAdapter")
except ImportError:
    pass
