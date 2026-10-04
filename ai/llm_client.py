from abc import ABC, abstractmethod
from typing import Optional


class LLMClient(ABC):
    """
    Abstract interface for all LLM providers.

    The rest of the application communicates through this
    interface instead of directly depending on a specific
    LLM provider.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        response_format: Optional[str] = None
    ) -> str:
        """
        Generate a response from the LLM.

        response_format:
            "json"  -> structured JSON response
            None    -> normal text response
        """
        pass


class OllamaLLMClient(LLMClient):

    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url

    def generate(
        self,
        prompt: str,
        response_format: Optional[str] = None
    ) -> str:

        import requests

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if response_format == "json":
            payload["format"] = "json"

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=400
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]


if __name__ == "__main__":

    client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    print("\nTesting normal text response...\n")

    response = client.generate(
        "Answer this in one short sentence: "
        "Which region generated the most revenue?"
    )

    print(response)

    print("\nTesting JSON response...\n")

    response = client.generate(
        'Return JSON with one key called "query".',
        response_format="json"
    )

    print(response)