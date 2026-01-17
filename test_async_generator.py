#!/usr/bin/env python3
import asyncio
from ai_conversation import ConversationManager

# 测试异步生成器装饰器修复
def test_async_generator():
    print("Testing async generator decorator fix...")
    
    # 创建ConversationManager实例
    manager = ConversationManager()
    
    # 测试异步生成器函数
    async def test_process_user_input_stream():
        print("\nTesting process_user_input_stream...")
        try:
            # 测试使用async for迭代
            user_text = "你好，小叶同学"
            
            print(f"Testing with input: {user_text}")
            
            # 这里应该能够正常迭代，不会抛出类型错误
            full_response = ""
            async for chunk in manager.process_user_input_stream(user_text):
                print(f"Received chunk: {chunk}")
                full_response += chunk
            
            print(f"Full response: {full_response}")
            print("✅ Async generator test passed!")
            return True
        except Exception as e:
            print(f"❌ Async generator test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 运行测试
    success = asyncio.run(test_process_user_input_stream())
    
    if success:
        print("\n✅ All tests passed! The async generator decorator fix is working correctly.")
    else:
        print("\n❌ Some tests failed. The fix may not be complete.")

if __name__ == "__main__":
    test_async_generator()
