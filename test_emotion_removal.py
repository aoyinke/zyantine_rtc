#!/usr/bin/env python3
"""
测试情绪标签移除功能
"""

from ai_conversation import AIConversation

# 创建AIConversation实例
ai_conv = AIConversation()

# 测试用例
test_cases = [
    # 纯文本情绪词
    "帅雄...你最近是不是压力太大了？公务员面试准备得怎么样了？neutral",
    # 带空格的纯文本情绪词
    "帅雄...你最近是不是压力太大了？公务员面试准备得怎么样了？  neutral  ",
    # 格式化情绪标签
    "帅雄...你最近是不是压力太大了？公务员面试准备得怎么样了？[EMOTION:neutral]",
    # 带空格的格式化情绪标签
    "帅雄...你最近是不是压力太大了？公务员面试准备得怎么样了？  [EMOTION:neutral]  ",
    # 其他情绪类型
    "我很高兴见到你！happy",
    "今天天气真糟糕。sad",
    "你太棒了！excited",
    # 正常文本（无情绪标签）
    "帅雄...你最近是不是压力太大了？公务员面试准备得怎么样了？",
    "我很高兴见到你！",
]

print("测试情绪标签移除功能...\n")

for i, test_text in enumerate(test_cases, 1):
    result = ai_conv.remove_emotion_tag(test_text)
    print(f"测试用例 {i}:")
    print(f"输入: '{test_text}'")
    print(f"输出: '{result}'")
    print(f"是否移除了情绪标签: {result != test_text}")
    print()

print("测试完成！")
