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
    folder_path = 'D:\\00LLMScenario\\dataset\\intersection'
    target_folder_path = 'D:\\pythonProject\\LLM_Scenario\\new_structured_risk_without_cot\\gemma'
    os.makedirs(target_folder_path, exist_ok=True)
    # os.makedirs(all_path, exist_ok=True)



    task ="""You are an accident analysis expert with extensive knowledge in the traffic field. Extract the risk factors that directly or potentially contributed to the first collision from the accident report below, and output the results in JSON format. Do not output in markdown format.

Task Requirements:
Read the accident report and identify all risk factors that directly or indirectly contributed to the first collision.
Focus only on information related to the events leading up to the first collision.
Ignore all factors, events, or consequences occurring after the first collision.
Exclude driver-related subjective factors such as age, experience, intent, emotion, psychological state, or medical background unless they are explicitly represented as observable traffic risk factors in the Restricted Risk Factor List.
Strictly restrict the extracted factors to the "Restricted Risk Factor List" below.
If an important risk factor is present in the report but is not included in the list, place it under "Other Relevant Risk Layer".
Only extract factors whose manifestation corresponds to Level 2 or higher.
Do not extract any factor whose state is Level 1, even if it is mentioned in the report.

Output Format:
Output only one JSON object.
Include [JSON] at the beginning of the output and [/JSON] at the end.

The JSON structure must be:
{
"risk_factor_classification": {
"Road Layer": [...],
"Infrastructure Layer": [...],
"Object Interaction Layer": [...],
"Environment Layer": [...],
"Other Relevant Risk Layer": [...]
}
}

Each extracted risk factor must contain exactly the following three fields:
"Risk Factor": use the exact factor name from the "Risk Factor" column in the Restricted Risk Factor List.
"Risk Level": use the exact level name from the "Level Settings" that matches the report description.
"Specific Description": explain how the factor contributed to the first collision based on the accident report. The explanation must include both the report evidence and a brief analysis of the factor's role in the collision.

Extraction Constraints:
Only include factors that played a direct or indirect role in causing the first collision.
Only include factors whose state corresponds to Level 2 or higher.
Do not include default safe conditions.
Do not include explanatory text outside the JSON object.


"""
    level = read_file('/g_prompt/e_intersection_level.txt')

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            target_file_path = os.path.join(target_folder_path, filename)
            summary = read_file(file_path)
            prompt =  task + '\n' + 'summary:' + '\n' + summary + '\n' + 'level:'+ level
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
