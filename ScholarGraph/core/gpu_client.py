"""
GPU Rig client for generating embeddings and text using Qwen or Mistral models.
"""

from typing import Optional, List
import requests
from config import get_settings
from .retry_handler import retry_with_exponential_backoff


class GPURigClient:
    """
    Client for interacting with GPU rig for LLM inference and embedding generation.

    Supports:
    - Qwen 2.5 7B (port 8000)
    - Mistral 7B (port 8001)
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize GPU rig client.

        Args:
            model: Model to use ("qwen" or "mistral"). Defaults to settings.
        """
        settings = get_settings()

        self.model = model or settings.embedding_model

        if self.model.lower() == "qwen":
            self.api_url = settings.gpu_rig_qwen_url
        elif self.model.lower() == "mistral":
            self.api_url = settings.gpu_rig_mistral_url
        else:
            raise ValueError(f"Unknown model: {self.model}. Use 'qwen' or 'mistral'")

        self.query_endpoint = f"{self.api_url}/query"

        # Embedding server URL (separate from LLM endpoints)
        self.embedding_url = settings.gpu_rig_embedding_url

    @retry_with_exponential_backoff(
        max_attempts=5,
        exceptions=(
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
        )
    )
    def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using the GPU rig LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text

        Example:
            client = GPURigClient()
            response = client.generate_text("What is federated learning?")
        """
        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:" if system_prompt else prompt

        response = requests.post(
            self.query_endpoint,
            json={
                "prompt": full_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=120  # 2 minute timeout for GPU processing
        )

        response.raise_for_status()

        data = response.json()

        # Extract generated text from response
        # Response format may vary - adjust based on actual API
        if isinstance(data, dict):
            return data.get("response", data.get("text", str(data)))
        else:
            return str(data)

    @retry_with_exponential_backoff(
        max_attempts=5,
        exceptions=(
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
        )
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using dedicated embedding server.

        Uses nomic-embed-text-v1.5 model on port 8005 with OpenAI-compatible API.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector (768 dimensions)

        Raises:
            NotImplementedError: If embedding endpoint is not available
        """
        # Use OpenAI-compatible API format
        embedding_endpoint = f"{self.embedding_url}/v1/embeddings"

        try:
            response = requests.post(
                embedding_endpoint,
                json={"input": text},
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            # OpenAI-compatible format: {"data": [{"embedding": [...]}]}
            if isinstance(data, dict) and "data" in data:
                if len(data["data"]) > 0 and "embedding" in data["data"][0]:
                    return data["data"][0]["embedding"]

            raise ValueError(f"Unexpected response format: {data}")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise NotImplementedError(
                    "Embedding endpoint not available. "
                    "Consider using sentence-transformers for embeddings."
                )
            raise

    def test_connection(self) -> dict:
        """
        Test connection to GPU rig.

        Returns:
            Dictionary with connection status
        """
        try:
            response = requests.post(
                self.query_endpoint,
                json={
                    "prompt": "test",
                    "max_tokens": 5,
                    "temperature": 0.1
                },
                timeout=10
            )

            if response.status_code == 200:
                return {
                    "status": "connected",
                    "model": self.model,
                    "url": self.api_url,
                    "message": "GPU rig is responding"
                }
            else:
                return {
                    "status": "error",
                    "model": self.model,
                    "url": self.api_url,
                    "message": f"Got status code {response.status_code}"
                }

        except Exception as e:
            return {
                "status": "error",
                "model": self.model,
                "url": self.api_url,
                "message": str(e)
            }


if __name__ == "__main__":
    # Test GPU rig connection
    print("Testing GPU rig connections...")

    for model in ["qwen", "mistral"]:
        print(f"\n{'='*50}")
        print(f"Testing {model.upper()} model...")
        print('='*50)

        try:
            client = GPURigClient(model=model)

            # Test connection
            status = client.test_connection()
            print(f"\nConnection Status: {status}")

            if status["status"] == "connected":
                # Test text generation
                print("\nTesting text generation...")
                response = client.generate_text(
                    "What is 2+2?",
                    max_tokens=50,
                    temperature=0.1
                )
                print(f"Response: {response[:200]}...")

        except Exception as e:
            print(f"Error: {e}")
