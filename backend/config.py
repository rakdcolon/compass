import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# Amazon Nova Model IDs
# Cross-region inference profiles (us. prefix) require bedrock:InvokeModel on
# arn:aws:bedrock:*:*:inference-profile/* in your IAM policy.
# Override via env vars if needed (e.g. NOVA_LITE_MODEL_ID=amazon.nova-lite-v1:0)
NOVA_LITE_MODEL_ID = os.getenv("NOVA_LITE_MODEL_ID", "us.amazon.nova-lite-v1:0")
NOVA_SONIC_MODEL_ID = os.getenv("NOVA_SONIC_MODEL_ID", "amazon.nova-2-sonic-v1:0")
NOVA_EMBEDDINGS_MODEL_ID = os.getenv("NOVA_EMBEDDINGS_MODEL_ID", "amazon.nova-2-multimodal-embeddings-v1:0")

# Nova Act
NOVA_ACT_API_KEY = os.getenv("NOVA_ACT_API_KEY", "")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Nova Sonic Audio Config
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_BIT_DEPTH = 16

# Nova Sonic Voice Options
NOVA_SONIC_VOICES = {
    "en": "matthew",
    "es": "lucia",
    "fr": "isabelle",
}

# Inference parameters
NOVA_LITE_MAX_TOKENS = 2048
NOVA_LITE_TEMPERATURE = 0.4
NOVA_LITE_TOP_P = 0.9

# Embedding dimensions
EMBEDDING_DIMENSION = 1024

# 2024 Federal Poverty Level (FPL) Annual Thresholds by household size
FPL_2024 = {
    1: 15060,
    2: 20440,
    3: 25820,
    4: 31200,
    5: 36580,
    6: 41960,
    7: 47340,
    8: 52720,
}

def get_fpl(household_size: int) -> int:
    if household_size <= 8:
        return FPL_2024.get(household_size, FPL_2024[8])
    return FPL_2024[8] + (household_size - 8) * 5380
