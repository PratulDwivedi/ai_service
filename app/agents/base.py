from abc import ABC, abstractmethod


class Agent(ABC):
    """Base class for AI agents. Implement `run` with your logic."""

    def __init__(self, **kwargs):
        self.config = kwargs

    @abstractmethod
    def run(self, *args, **kwargs):
        raise NotImplementedError


# example of specialized agent

class ChatAgent(Agent):
    def run(self, prompt: str) -> str:
        # placeholder for integration with OpenAI/other LLM
        return f"Echo: {prompt}"
