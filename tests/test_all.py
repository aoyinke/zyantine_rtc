import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test_stt():
    """Run STT tests"""
    logger.info("\n=== Running STT Tests ===")
    try:
        from test_stt import main as stt_main
        await stt_main()
        logger.info("STT tests completed")
        return True
    except Exception as e:
        logger.error(f"Error running STT tests: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_test_tts():
    """Run TTS tests"""
    logger.info("\n=== Running TTS Tests ===")
    try:
        from test_tts import main as tts_main
        result = await tts_main()
        logger.info(f"TTS tests completed with exit code: {result}")
        return result == 0
    except Exception as e:
        logger.error(f"Error running TTS tests: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_test_tts_voices():
    """Run TTS voices test"""
    logger.info("\n=== Running TTS Voices Test ===")
    try:
        from test_tts_voices import test_voices
        await test_voices()
        logger.info("TTS voices test completed")
        return True
    except Exception as e:
        logger.error(f"Error running TTS voices test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_test_volcengine_tts():
    """Run VolcEngine TTS test"""
    logger.info("\n=== Running VolcEngine TTS Test ===")
    try:
        from test_volcengine_tts import test_volcengine_tts
        await test_volcengine_tts()
        logger.info("VolcEngine TTS test completed")
        return True
    except Exception as e:
        logger.error(f"Error running VolcEngine TTS test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    logger.info("Starting all tests...")
    
    # Run tests sequentially
    tests = [
        run_test_stt,
        run_test_tts,
        run_test_tts_voices,
        run_test_volcengine_tts
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    test_names = ["STT", "TTS", "TTS Voices", "VolcEngine TTS"]
    passed_count = sum(results)
    total_count = len(results)
    
    for name, passed in zip(test_names, results):
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        logger.info("\n🎉 All tests passed!")
        return 0
    else:
        logger.error("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)