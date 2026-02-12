#!/usr/bin/env python3
"""
Pre-build the embeddings cache locally.

Run this on a machine with enough RAM (laptop / CI), then copy the generated
.embeddings_cache.pkl to the production server so that the server never needs
to load the SentenceTransformer model for the initial build.

Usage:
    cd <project-root>
    python -m scripts.build_embedding_cache          # build (skip if fresh)
    python -m scripts.build_embedding_cache --force   # force rebuild
"""

import argparse
import os
import sys

# Ensure the project root is on sys.path so 'app' is importable
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.llm.embedding_service import EmbeddingService


def main():
    parser = argparse.ArgumentParser(description="Pre-build embeddings cache")
    parser.add_argument(
        "--force", action="store_true", help="Force rebuild even if cache exists"
    )
    args = parser.parse_args()

    service = EmbeddingService()
    service.build_embeddings(force_rebuild=args.force)

    cache_path = os.path.join(project_root, ".embeddings_cache.pkl")
    if os.path.exists(cache_path):
        size_mb = os.path.getsize(cache_path) / (1024 * 1024)
        print(f"\n✅ Cache ready: {cache_path} ({size_mb:.1f} MB)")
        print(f"   Copy this file to the server's project root.")
    else:
        print("\n❌ Cache file was not created. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
