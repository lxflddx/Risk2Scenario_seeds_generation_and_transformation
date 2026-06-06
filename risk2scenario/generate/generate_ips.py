import re
import traceback

import time
from risk2scenario.utils.llm_util import request_response
# from utils.openai_llm_utils import request_response

OPENROUTER_API_KEY = 'your key'
"""
生成交互模式序列
"""
# url = "https://openrouter.ai/api/v1/chat/completions"
start_time = time.time()


class ExtractIps:
    def __init__(self):
        self.role_prompt = ("You are an expert in Simulation-based Testing for Autonomous Driving Systems, "
                            "with the goal of extracting functional scenarios from public accident reports. "
                            "Here is a description of an accident report: ")
        self.task_summarize_prompt = (
            "Please provide the following details for the given scenario:\n"
            "Important: Lane IDs increase from right to left.Lane 1 is the rightmost lane, Lane 2 is the second rightmost lane, and so on.\n"
            "Environment: Describe the environment where the scenario takes place, including weather conditions and road surface conditions.\n"
            "Road Structure: Specify the road structure (e.g., 'straight 4-lane road').\n"
            "Initial Actions: List the initial actions of ALL vehicles in the format: (V1): V1 drives on Lane X...; (V2): V2 drives on Lane Y...;by extracting EVERY vehicle information and representing each vehicle with a unique numerical identifier (e.g., V1, V2, V3, etc.), and indicating the lane number (e.g., Lane 1, Lane 2, Lane 3) based on the available information in the crash report.\n"
            "Interactive Pattern Sequence: Describe the interactions between pairs of vehicles in the format: '(Vi, Vj): action description of Vi and Vj.' by representing each vehicle with a unique numerical identifier (e.g., V1, V2, V3, etc.).\n"
            "Ensure that each interactive pattern only contains two vehicles and follows the specified format."
            "Candidate Ego Vehicle: Select the most passive vehicle from the two vehicles involved in the first collision to be the ego vehicle in this scenario, and output it in the format: Candidate Ego: Vx (where Vx is the vehicle identifier, e.g., V2)."
        )
        # self.task_summarize_prompt = (
        #     "Please provide the following details for the given scenario:\n"
        #     "Important: Lane IDs increase from right to left.Lane 1 is the rightmost lane, Lane 2 is the second rightmost lane, and so on.\n"
        #     "Environment: Describe the environment where the scenario takes place, including weather conditions and road surface conditions.\n"
        #     "Road Structure: Specify the road structure (e.g., 'straight 4-lane road').\n"
        #     "Initial Actions: List the initial actions of ALL vehicles in the format: (V1): V1 drives on Lane X...; (V2): V2 drives on Lane Y...;by extracting EVERY vehicle information and representing each vehicle with a unique numerical identifier (e.g., V1, V2, V3, etc.), and indicating the lane number (e.g., Lane 1, Lane 2, Lane 3) based on the available information in the crash report.\n"
        #     "Interactive Pattern Sequence: Describe the interactions between pairs of vehicles in the format: '(Vi, Vj): action description of Vi and Vj.' by representing each vehicle with a unique numerical identifier (e.g., V1, V2, V3, etc.).\n"
        #     "Ensure that each interactive pattern only contains two vehicles and follows the specified format."
        # )
        self.attention_summarize_prompt = (
            "Attention: "
            "1. DO NOT use markdown format for the output. Avoid any bold, italic, headers, or other formatting."
            "2. the action description should contain the relative road position of each vehicle and be in one sentence;"
            "3. the verb to describe each action should be selected from {brake, decelerate, accelerate, swerve left/right};"
            "4. do not involve the interactive pattern after the first crash occurs;"
            "5. focus on the vehicles' movement and do not describe the drivers' actions."
            "6. try to make the interactive pattern sequence as short as possible."
        )

    def extract(self, description):
        prompt = self.role_prompt + description + self.task_summarize_prompt + self.attention_summarize_prompt
        print("prompt:", prompt)
        response = request_response(prompt)
        print("response:", response)
        func_scenario, func_scenario_dict, candidate_ego = self.extract_scenario_dict(response)
        extracted_data = {"func_scenario": func_scenario, "func_scenario_dict": func_scenario_dict,
                          "candidate_ego": candidate_ego}  # 字典，包含功能场景、功能场景字典、候选ego
        print("extracted_data:", extracted_data)
        return extracted_data
        # 怎么处理后面再说，选定了模型之后再说

    @staticmethod
    def extract_scenario_dict(response):
        try:
            # 检查响应类型
            if response is None:
                print("Error: Response is None")
                return None

            # 如果是字典，提取 content 字段
            if isinstance(response, dict):
                content = response.get('choices', [{}]) [0].get('message', {}).get('content', '')
                if not content:
                    print("Error: No content found in response dictionary")
                    return None
            else:
                # 如果是字符串，解析 JSON
                import json
                response_dict = json.loads(response)
                content = response_dict.get('choices', [{}]) [0].get('message', {}).get('content', '')

            # 清洗响应内容，处理换行符和制表符
            lines = content.strip().splitlines()
            content = "\n".join(lines).replace("\n", "\\n").replace("\t", "\\t")
            print(f"content-------------------------{content}")

            # content = "\n".join(lines).replace("\n", "\\n").replace("\t", "\\t")    # gpt
            # print(f"content-------------------------{content}")
            # json_data = json.loads(content)  # gpt



            # 提取 JSON 数据中的关键内容
            # if isinstance(json_data, dict):
            #     content = json_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            #     print("content:\n", content, "\n")

                # 使用正则表达式提取环境、道路结构、初始动作和交互模式
            environment_match = re.search(r"Environment:\s*(.*?)(?=Road Structure:|\n\n$)", content, re.DOTALL)
            road_structure_match = re.search(r"Road Structure:\s*(.*?)(?=Initial Actions:|\n\n$)", content,
                                             re.DOTALL)
            initial_actions_match = re.search(r"Initial Actions:\s*(.*?)(?=Interactive Pattern Sequence:|\n\n$)",
                                              content, re.DOTALL)
            interactive_pattern_match = re.search(r"Interactive Pattern Sequence:\s*(.*?)(?=Candidate Ego:|\n\n$)",
                                                  content, re.DOTALL)
            candidate_ego_match = re.search(r"Candidate Ego:\s*(.*)", content, re.DOTALL)
            environment = environment_match.group(1).strip() if environment_match else ""
            road_structure = road_structure_match.group(1).strip() if road_structure_match else ""
            initial_actions = initial_actions_match.group(1).strip() if initial_actions_match else ""
            interactive_pattern = interactive_pattern_match.group(1).strip() if interactive_pattern_match else ""
            candidate_ego = candidate_ego_match.group(1).strip() if candidate_ego_match else ""
            # print(f"candidate_ego_match:{candidate_ego}")

            # # 提取车辆列表和频率字典
            # vehicle_list = re.findall(r'V\d+', response)
            # print("vehicle_list:", vehicle_list, "\n")
            # frequency_dict = {}
            # for v in set(vehicle_list):
            #     frequency_dict[v] = 0
            #
            # pattern_sequences = re.findall(r'\([^)]+\):\s*[^;]+', interactive_pattern)
            #
            # # 构造交互模式字典
            # pattern_dict = {}
            # for seq in pattern_sequences:
            #     key_value = seq.split(':', 1)  # 只分割第一个冒号
            #     if len(key_value) == 2:
            #         # 提取键并去除空格
            #         key_str = key_value[0].strip()[1:-1]  # 去掉括号
            #         key = tuple(item.strip() for item in key_str.split(',') if item.strip())  # 分割并过滤空值
            #
            #         # 检查键是否有效
            #         if all(item.startswith('V') or item == 'None' for item in key):
            #             value = key_value[1].strip()  # 提取值
            #             pattern_dict[key] = value
            #
            #             # 更新频率字典
            #             for item in key:
            #                 if item.startswith('V'):
            #                     frequency_dict[item] = frequency_dict.get(item, 0) + 1
            #
            # # 构造交互模式序列字符串
            # pattern_string = ""
            # for key, value in pattern_dict.items():
            #     key_str = ", ".join(key)
            #     pattern_string += f"({key_str}): {value}\n"
            #
            # # 找到出现频率最小的车辆作为候选 ego
            # min_value = min(frequency_dict.values())
            # candidate_ego = [key for key, value in frequency_dict.items() if value == min_value]
            # print("candidate_ego:", candidate_ego, "\n")

            # 构造功能场景字符串
            func_scenario = "Initial actions: \n" + initial_actions + "\n" + "Interactive pattern sequence: \n" + interactive_pattern

            # 构造功能场景字典
            func_scenario_dict = {
                "Environment": environment,
                "Road Structure": road_structure,
                "Initial Actions": initial_actions,
                "Interactive Pattern Sequence": interactive_pattern
            }
            # print("functional scenario: \n", func_scenario_dict)

            return func_scenario, func_scenario_dict, candidate_ego

        except Exception as e:
            print("error:", e)
            error_message = traceback.format_exc()
            print("Detailed error traceback:\n", error_message)
            return None


if __name__ == '__main__':
    # ontology_prompt = read_file("D:\\pythonProject\\LLM_Scenario\\g_prompt\\generate_ips.txt")
    # text = """
    extract_ips = ExtractIps()
    description = """(1) Initial Setup
On a one-way three-lane roadway with a 5% uphill grade, under unlit nighttime conditions, a continuous concrete barrier is present along the left side of Lane 3.

V1 is traveling in Lane 2 at 72 km/h, moving straight ahead.
V2 follows V1 in Lane 2 at a distance of approximately 25 meters, traveling at 78 km/h.
V3 is in Lane 3, slightly behind and parallel to V1 by about 10 meters, traveling at 80 km/h.
V4 is in Lane 1, approximately 30 meters behind V1, traveling steadily at 70 km/h.

(2) Scenario Development
While traveling uphill, V1 misjudges the forward traffic situation due to limited nighttime visibility and decelerates abruptly from 72 km/h to approximately 25 km/h.

V2 detects the deceleration at a short distance and applies emergency braking, reducing speed from 78 km/h to about 40 km/h, but continues closing in on V1.

V1, noticing the rapidly approaching V2, initiates a lane change to the left. Due to reduced acceleration capability on the uphill and its low speed, the lateral movement is slow and prolonged.

V3 continues in Lane 3 at 80 km/h and only recognizes V1’s lane intrusion when V1 has already occupied about half of the lane width. V3 brakes and slightly steers left, but cannot evade further due to the adjacent concrete barrier.

(3) Outcome
Before fully entering Lane 3, V1’s front-left side collides with V3’s front-right side. At impact, V1 is traveling at approximately 28 km/h and V3 at 65 km/h. After the collision, V3 loses stability and deflects leftward, contacting the concrete barrier. The incident blocks Lanes 2 and 3, causing following vehicles to slow down."""
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
# # {"id":"gen-1744712613-0dd8hvZbqnd25NJfQGVd","provider":"Chutes","model":"google/gemma-3-27b-it","object":"chat.completion","created":1744712613,"choices":[{"logprobs":null,"finish_reason":"stop","native_finish_reason":"stop","index":0,"message":{"role":"assistant","content":"\nEnvironment: The environment is a multi-lane highway_gemma with dry road conditions and clear weather, as no weather or road surface conditions are explicitly mentioned in the report, implying standard conditions.\n\nRoad Structure: Straight 3-lane road.\n\nInitial Actions: (V1): V1 drives on Lane 2 at a steady speed, initially ahead of V2; (V2): V2 drives on Lane 1 at a steady speed, slightly behind V1; (V3): V3 drives on Lane 3 approaching V1 from behind at a steady speed.\n\nInteractive Pattern Sequence: (V3, V1): V3 swerves right from Lane 3 to Lane 2, causing V1 to change its relative position; (V1, V2): V1 swerves right from Lane 2 to Lane 1, encroaching into V2’s lane; (V2, V1): V2 swerves right towards the shoulder as V1 encroaches into its lane; (V1, V2): V1 collides with V2 while attempting to avoid a crash.\n\ncandidate_ego: V2\n","refusal":null,"reasoning":null}}],"usage":{"prompt_tokens":756,"completion_tokens":235,"total_tokens":991}}"""
    response = extract_ips.extract(description)
    # extract_ips.extract_scenario_dict(response)
    end_time = time.time()
    run_time = end_time - start_time
    print(f"代码运行总时间: {run_time} 秒")
