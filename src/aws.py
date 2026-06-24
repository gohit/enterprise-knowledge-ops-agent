"""AWS Bedrock client helper.

Builds a single ``bedrock-runtime`` boto3 client used by both the chat model and the
embedding model. Explicit keys from settings are used when present; otherwise boto3's
default credential chain (env vars, shared config, SSO, or an IAM role) applies.
"""
from __future__ import annotations

from src.config import settings


def _client_kwargs() -> dict:
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            kwargs["aws_session_token"] = settings.aws_session_token
    return kwargs


def get_bedrock_runtime_client():
    """Runtime client for invoking models (InvokeModel / Converse)."""
    import boto3  # imported lazily so the package loads without boto3 installed

    return boto3.client("bedrock-runtime", **_client_kwargs())


def get_bedrock_client():
    """Control-plane client for listing models / inference profiles."""
    import boto3

    return boto3.client("bedrock", **_client_kwargs())
