import base64
import os
import requests
import json
import time
from risk2scenario.utils.file_util import read_file

"""
LLM提取风险因素，存储到json文件（可以多模态）
"""

OPENROUTER_API_KEY = 'your key'


url = "https://openrouter.ai/api/v1/chat/completions"
start_time = time.time()


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# Define the function to interact with the API
def LLM(prompt):
    # content = [
    #     {
    #         "type": "text",
    #         "text": ontology_prompt
    #     },
    #     {
    #         "type": "image_url",
    #         "image_url": {
    #             "url": f"data:image/jpeg;base64,{encoded_image}"
    #         }
    #     }
    # ]
    while True:
        try:
            response = requests.post(
                url=url,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                },
                data=json.dumps({
                    "model": "google/gemma-3-27b-it",  # Optional
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "top_p": 1,
                    "temperature": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                    "repetition_penalty": 1,
                    "top_k": 0,
                })
            )
            # Check if the request was successful
            print(response.status_code)
            parsed_response = json.loads(response.text)
            if 'error' in parsed_response:
                response_status_code = parsed_response['error']['code']
            else:
                response_status_code = None
            if response_status_code is None:
                print("response success")
                # print(response.text)
                return response.text
            elif response_status_code == 429:  # Too many requests
                print("Rate limit exceeded. Retrying after 20 seconds...")
                time.sleep(20)
            else:
                print(f"Error: {response.status_code}, {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}. Retrying in 15 seconds...")
            time.sleep(15)


if __name__ == '__main__':
    # ontology_prompt = read_file('D:\\pythonProject\\LLM_Scenario\\g_prompt\\risk_extract_prompt.txt')
    # image_path = 'D:\\pythonProject\\LLM_Scenario\\data\\image\\img.png'
    # encoded_image = encode_image(image_path)
    #
    # result = LLM(ontology_prompt)
    # if result:
    #     result = result.replace("\\n", "\n")
    #     print(result)

    # -------------------------------单个和批量测试--------------------
    all_path = '/g_risky_reports_output/new_structured_risk_reports_output_in_all_highway_qwen.txt'
    folder_path = 'D:\\00LLMScenario\\dataset\\1'
    target_folder_path = 'D:\\pythonProject\\LLM_Scenario\\new_structured_risk_without_cot\\with_cot_gemma'
    os.makedirs(target_folder_path, exist_ok=True)
    # os.makedirs(all_path, exist_ok=True)


    sys = read_file('D:\\pythonProject\\LLM_Scenario\\g_prompt\\e_sys.xt')
    task = read_file('/g_prompt/e_task.txt')
    level = read_file('/g_prompt/e_intersection_level.txt')

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            target_file_path = os.path.join(target_folder_path, filename)
            summary = read_file(file_path)
            prompt = sys + task + '\n' + 'summary:' + '\n' + summary + '\n' + level
            print(prompt)
            result = LLM(prompt)
            if result:
                result = result.replace("\\n", "\n")
                print(result)
                with open(target_file_path, 'w', encoding='utf-8') as target_file:
                    target_file.write(result)
                # print(f"Saved result to {target_file_path}")
                # with open(all_path, 'a', encoding='utf-8') as target_file:
                #     target_file.write(result)
    #
    # Ensure we don't exceed the rate limit
    # time.sleep(40)

    end_time = time.time()
    run_time = end_time - start_time
    print(f"Total runtime: {run_time} seconds")
