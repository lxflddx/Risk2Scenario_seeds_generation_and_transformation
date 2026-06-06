import openai
import time

# 初始化 OpenAI 客户端
client = openai.Client(
    api_key="your openai key",
    timeout=150
)


def request_response (content):
    """
    调用 OpenAI API 并获取响应
    :param content: 用户输入的内容
    :return: API 返回的响应文本，或者 None（如果发生错误）
    """
    while True:
        try:
            # 准备对话消息
            messages = [
                {"role": "user", "content": content}
            ]

            # 调用模型生成
            completion = client.chat.completions.create(
                model="gpt-4.1",
                messages=messages,
                temperature=0.7  # 控制输出的随机性
            )

            # 获取结果
            result = completion.choices [0].message.content
            return result
        except openai.error.APIError as e:
            print(f"OpenAI API error: {e}")
            if e.is_rate_limit_error():
                print("Rate limit exceeded. Retrying after 40 seconds...")
                time.sleep(40)
            else:
                return None
        except Exception as e:
            print(f"Request failed: {e}. Retrying in 15 seconds...")
            time.sleep(15)


# 示例调用
if __name__ == "__main__":
    # 示例文本
    start_time = time.time()
    example_text = """下午好"""
    result = request_response(example_text)
    if result:
        print(result)
    end_time = time.time()
    print("Time used:", end_time - start_time)
