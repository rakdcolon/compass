#!/usr/bin/env python3
"""
Compass AI Benefits Navigator
Entry point for the application.

Usage:
    python run.py              # Start server (default: http://localhost:8000)
    python run.py --port 3000  # Custom port
    python run.py --demo       # Print demo instructions
"""

import argparse
import sys
import os

def check_env():
    """Check required environment variables and warn if missing."""
    missing = []
    warnings = []

    # Check for AWS credentials
    has_key = bool(os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE"))
    has_region = bool(os.getenv("AWS_DEFAULT_REGION"))

    if not has_key:
        missing.append("AWS credentials (AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY, or AWS_PROFILE)")
    if not has_region:
        warnings.append("AWS_DEFAULT_REGION not set — defaulting to us-east-1")

    if not os.getenv("NOVA_ACT_API_KEY"):
        warnings.append("NOVA_ACT_API_KEY not set — Nova Act portal automation will show manual instructions")

    if missing:
        print("\n⚠️  Missing required configuration:")
        for m in missing:
            print(f"   • {m}")
        print("\nCopy .env.example to .env and fill in your credentials:")
        print("   cp .env.example .env")
        print("\nThen re-run: python run.py\n")
        return False

    if warnings:
        print("\n📝 Notes:")
        for w in warnings:
            print(f"   • {w}")

    return True


def print_demo_info():
    """Print demo usage instructions."""
    print("""
╔════════════════════════════════════════════════════════════╗
║         COMPASS - AI Benefits Navigator                     ║
║         Amazon Nova Hackathon Submission                    ║
╚════════════════════════════════════════════════════════════╝

DEMO FLOW:
─────────
1. Open http://localhost:8000 in your browser
2. Click the microphone button and say:
   "I lost my job last month and I'm struggling to pay
    for groceries and my kids need healthcare. I live in
    California with my 2 kids. We make about $2,000 a month."

3. Compass (Nova 2 Sonic) will ask follow-up questions
4. Upload a pay stub image to trigger Nova vision analysis
5. See eligible programs (SNAP, Medicaid, TANF, WIC)
6. Click "Nova Act → Auto-fill" to trigger portal automation
7. View your personalized action plan

AMAZON NOVA MODELS USED:
─────────────────────────
• Nova 2 Lite      → Multi-agent orchestrator with tool use
• Nova 2 Sonic     → Real-time voice conversation
• Nova Embeddings  → Document-to-program semantic matching
• Nova Act         → Automated portal navigation

SOCIAL IMPACT:
──────────────
• $30B in benefits go unclaimed annually
• 7M eligible Americans don't receive SNAP
• 60% of eligible seniors miss Medicare Savings Programs
• Compass bridges this gap through accessible AI

API ENDPOINTS:
──────────────
POST /api/chat          - Text conversation (Nova 2 Lite)
POST /api/document      - Document upload (Nova vision + embeddings)
POST /api/navigate      - Portal automation (Nova Act)
WS   /ws/voice/{id}    - Voice streaming (Nova 2 Sonic)
GET  /api/session/{id}  - Get session state
""")


def main():
    parser = argparse.ArgumentParser(description="Compass AI Benefits Navigator")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--demo", action="store_true", help="Print demo instructions")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload (development)")
    args = parser.parse_args()

    if args.demo:
        print_demo_info()
        return

    # Load .env if present
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded .env file")

    print("""
╔═══════════════════════════════════════╗
║  Compass - AI Benefits Navigator      ║
║  Powered by Amazon Nova               ║
╚═══════════════════════════════════════╝
""")

    if not check_env():
        sys.exit(1)

    import uvicorn

    print(f"Starting server at http://localhost:{args.port}")
    print(f"Open http://localhost:{args.port} in your browser\n")

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
