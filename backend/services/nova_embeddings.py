"""
Amazon Nova Multimodal Embeddings service.
Used to embed benefit program descriptions and uploaded documents
for semantic similarity matching.
"""

import base64
import json
import logging
import math
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from backend.config import AWS_REGION, NOVA_EMBEDDINGS_MODEL_ID, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


class NovaEmbeddingsService:
    """Client for Amazon Nova Multimodal Embeddings via Bedrock."""

    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        self.model_id = NOVA_EMBEDDINGS_MODEL_ID
        self._program_embeddings: dict[str, list[float]] = {}

    def embed_text(self, text: str) -> list[float]:
        """
        Generate a text embedding using Nova multimodal embeddings.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        request_body = {
            "taskType": "SINGLE_EMBEDDING",
            "singleEmbeddingParams": {
                "embeddingDimension": EMBEDDING_DIMENSION,
                "text": {
                    "truncationMode": "END",
                    "value": text,
                },
            },
        }

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                accept="application/json",
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            return result["embedding"]
        except ClientError as e:
            logger.error("Nova Embeddings text error: %s", e)
            raise

    def embed_image(
        self,
        image_base64: str,
        image_format: str = "jpeg",
    ) -> list[float]:
        """
        Generate an image embedding using Nova multimodal embeddings.

        Args:
            image_base64: Base64-encoded image data
            image_format: Image format ('jpeg', 'png', 'webp')

        Returns:
            List of floats representing the embedding vector
        """
        request_body = {
            "taskType": "SINGLE_EMBEDDING",
            "singleEmbeddingParams": {
                "embeddingDimension": EMBEDDING_DIMENSION,
                "image": {
                    "format": image_format,
                    "source": {"bytes": image_base64},
                },
            },
        }

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                accept="application/json",
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            return result["embedding"]
        except ClientError as e:
            logger.error("Nova Embeddings image error: %s", e)
            raise

    def embed_document_image(
        self,
        image_base64: str,
        image_format: str = "jpeg",
    ) -> list[float]:
        """Embed a document image for similarity comparison with benefit programs."""
        return self.embed_image(image_base64, image_format)

    def precompute_program_embeddings(self) -> None:
        """
        Pre-compute embeddings for all benefit programs.
        Call this at startup to enable fast document-to-program matching.
        """
        from backend.data.benefits_db import BENEFITS_PROGRAMS

        logger.info("Pre-computing benefit program embeddings...")
        for program in BENEFITS_PROGRAMS:
            # Create a rich text description for embedding
            program_text = (
                f"{program['name']}: {program['description']} "
                f"Category: {program['category']}. "
                f"Tags: {', '.join(program.get('tags', []))}."
            )
            try:
                embedding = self.embed_text(program_text)
                self._program_embeddings[program["id"]] = embedding
                logger.debug("Embedded program: %s", program["id"])
            except Exception as e:
                logger.warning("Failed to embed program %s: %s", program["id"], e)

        logger.info("Pre-computed embeddings for %d programs", len(self._program_embeddings))

    def find_matching_programs(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Find benefit programs most similar to a query embedding.

        Args:
            query_embedding: Embedding of query text or document image
            top_k: Number of top results to return

        Returns:
            List of dicts with program_id, name, similarity_score
        """
        from backend.data.benefits_db import BENEFITS_BY_ID

        if not self._program_embeddings:
            logger.warning("No program embeddings available; call precompute_program_embeddings first")
            return []

        scores = []
        for program_id, program_embedding in self._program_embeddings.items():
            score = cosine_similarity(query_embedding, program_embedding)
            scores.append((program_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        results = []
        for program_id, score in top_results:
            program = BENEFITS_BY_ID.get(program_id, {})
            results.append({
                "id": program_id,
                "name": program.get("name", program_id),
                "category": program.get("category", ""),
                "similarity_score": round(score, 4),
                "similarity_pct": f"{score * 100:.1f}%",
            })

        return results

    def find_programs_for_document(
        self,
        image_base64: str,
        image_format: str = "jpeg",
        top_k: int = 5,
    ) -> list[dict]:
        """
        Given a document image, find the most relevant benefit programs.

        Args:
            image_base64: Base64-encoded document image
            image_format: Image format
            top_k: Number of results

        Returns:
            List of matching programs with similarity scores
        """
        doc_embedding = self.embed_document_image(image_base64, image_format)
        return self.find_matching_programs(doc_embedding, top_k=top_k)

    def find_programs_for_text(self, text: str, top_k: int = 5) -> list[dict]:
        """
        Given a text description of a situation, find the most relevant programs.

        Args:
            text: Description of user's situation
            top_k: Number of results

        Returns:
            List of matching programs with similarity scores
        """
        text_embedding = self.embed_text(text)
        return self.find_matching_programs(text_embedding, top_k=top_k)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        raise ValueError(f"Vector dimension mismatch: {len(a)} vs {len(b)}")

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)
