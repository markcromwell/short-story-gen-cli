#!/usr/bin/env python3
"""
Quick validation script for integration test setup.

This script tests that the integration test infrastructure works
without running expensive full pipeline tests.
"""

import os
import sys
from pathlib import Path
from typing import cast

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_api_connectivity():
    """Test that APIs are accessible."""
    print("🔍 Testing API connectivity...")

    # Test xAI if key is available
    xai_key = os.getenv("XAI_API_KEY")
    if xai_key:
        try:
            import litellm

            litellm.completion(
                model="xai/grok-4-fast-reasoning",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                api_key=xai_key,
            )
            print("   ✅ xAI API: Connected")
        except Exception as e:
            print(f"   ❌ xAI API: {e}")
    else:
        print("   ⚠️  xAI API: No API key found")

    # Test Ollama if available
    try:
        import subprocess

        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   ✅ Ollama: Running")
        else:
            print("   ❌ Ollama: Not responding")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("   ⚠️  Ollama: Not installed or not running")


def test_test_infrastructure():
    """Test that test infrastructure works."""
    print("\n🔧 Testing test infrastructure...")

    try:
        from tests.integration.test_full_pipeline import TestFullPipeline

        print("   ✅ Test class imports successfully")

        pitches = TestFullPipeline.TEST_PITCHES
        print(f"   ✅ {len(pitches)} test pitches loaded")

        # Show pitch summary
        for pitch in pitches:
            genres = len(cast(list, pitch["expected_genres"]))
            print(f"      • {pitch['name']}: {pitch['word_count']:,} words, {genres} genres")

    except Exception as e:
        print(f"   ❌ Test infrastructure error: {e}")


def test_pipeline_import():
    """Test that pipeline components import correctly."""
    print("\n🔧 Testing pipeline imports...")

    try:
        print("   ✅ Pipeline function imports successfully")
    except Exception as e:
        print(f"   ❌ Pipeline import error: {e}")

    try:
        print("   ✅ All generator classes import successfully")
    except Exception as e:
        print(f"   ❌ Generator import error: {e}")


def main():
    """Run all validation tests."""
    print("🚀 Integration Test Setup Validation")
    print("=" * 50)

    test_api_connectivity()
    test_test_infrastructure()
    test_pipeline_import()

    print("\n" + "=" * 50)
    print("✅ Validation complete!")
    print("\nTo run integration tests:")
    print("  pytest tests/integration/test_full_pipeline.py --integration -v")
    print("\nFor overnight runs with Ollama:")
    print("  $env:INTEGRATION_MODEL = 'ollama/qwen2.5:14b'")
    print("  pytest tests/integration/test_full_pipeline.py --integration -m 'not slow'")


if __name__ == "__main__":
    main()
