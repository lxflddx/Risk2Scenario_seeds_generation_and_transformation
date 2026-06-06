import ast
import os
import re

import astunparse
import json
import time
from risk2scenario.utils.llm_util import request_response
# from utils.openai_llm_utils import request_response
from testcase import TestCase
from statement import ConstructorStatement, MethodStatement

# OPENROUTER_API_KEY = 'your key'
#
# url = "https://openrouter.ai/api/v1/chat/completions"
start_time = time.time()


class IpsToTestcase:
    def __init__(self):
        self.role_prompt = (
            "You are an expert in Simulation-based Testing for Autonomous Driving Systems, with the goal of "
            "generating logical test cases with suitable parameter ranges that correspond to functional scenario "
            "descriptions. Remember the scenario model and test case model provided in the initial ontology_prompt. Do not "
            "reproduce them in subsequent responses.  Focus solely on generating the test case for the provided "
            "scenario description.")
        self.intro_gen_testcase = "Here is the scenario model and the test case model: "
        path = os.path.dirname(os.path.abspath(__file__))
        with open(path + '/scenario_model.py', 'r') as f:
            self.scenario_model = f.read()
        self.testcase_example = ("def testcase(): \n"
                                 "  vehicle1 = NPC(lane_id= , offset= , initial_speed= ) \n"
                                 "  vehicle2 = NPC(lane_id= , offset= , initial_speed= ) \n"
                                 "  \n "
                                 "  vehicle1.decelerate(target_speed= , trigger_sequence= ) \n"
                                 "  vehicle2.changeLane(target_lane= , target_speed= , trigger_sequence= )"
                                 )
        self.test_case_model_attention = ("Attention:\n"
                                          "1. Treat merging and diverging as special cases of lane changing:\n"
                                          "   Merging: Vehicles changing from a ramp lane to a main road lane.\n"
                                          "2. When using the `changeLane` method:\n"
                                          "For merging, ensure that the target lane is on the main road and provide "
                                          "the necessary speed "
                                          "adjustment.\n "
                                          "3. The unit of speed is kilometers per hour (km/h)."
                                          )

        self.task_ge_testcase = ("For the following scenario description, generate a test case in the format "
                                 "provided.  Crucially, *all* parameter values (lane_id, offset, initial_speed, "
                                 "target_speed) must be specified as a range `[min_value, max_value]`.  Even if you "
                                 "believe a single value is appropriate, represent it as a range where the minimum "
                                 "and maximum values are equal (e.g., `[20.0, 20.0]`).  Provide positive ranges.\n"
                                 "Consider the scenario description carefully and choose ranges that are logically "
                                 "consistent with the events described; ranges should enable the scenario to reliably "
                                 "occur within a simulation."
                                 )
        self.ips = """Initial actions: 
(V1, V2, V3): V1 is traveling eastbound in the right lane approaching a T-intersection_gemma, V2 is also traveling eastbound in the right lane directly in front of V1 and decelerating, and V3 is traveling eastbound in the right lane directly 3-4 car lengths in front of V2.

Interactive pattern sequence: 
(V2, V1): V2 decelerates in traffic while in the same lane in front of V1 who maintains speed.
(V3, V2): V3 stays stationary due to traffic while V2 is decelerating directly behind it.
(V1, V2): V1 brakes and swerves right after noticing V2's abrupt deceleration.
(V3, V2): V3 attempts to turn wheel to the right upon noticing V1's high speed approach towards V2.
        """
        self.attention_gen_testcase = ("Attention:\n"
                                       "1. Treat merging and diverging as special cases of lane changing.\n"
                                       "2. When using the `changeLane` method: For merging, ensure that the target "
                                       "lane is on the main road and provide necessary speed adjustment.\n"
                                       "3. Lane IDs increase from right to left, starting at 1 to 5 (Lane 1 is the "
                                       "right-most lane, Lane 5 is the left-most, and DO NOT exceed [1,5]).If the "
                                       "crash report describes 3 lanes, then the lane ID for the left-most lane is "
                                       "3.\n "
                                       "4. Each method call should correspond to an action described in the "
                                       "functional scenario.\n"
                                       "5. Vehicle objects are named 'vehicle{1-n}'.\n"
                                       "6. Include comments to describe each action in the test case.\n"
                                       "7. do not add other actions such as the towing action.\n"
                                       "8. the maximum value of trigger_sequence is 5.\n"
                                       "9. Use triple backticks (```) to mark the beginning and end of code blocks to ensure clarity and readability."
                                       )

    def convert(self, extracted_data):
        # initial_actions = extracted_data["Initial Actions"]
        # interactive_pattern_sequence = extracted_data["Interactive Pattern Sequence"]
        prompt1 = self.role_prompt + "\n"+ self.intro_gen_testcase + "\n" + self.scenario_model + "\n" + self.testcase_example + "\n" + \
                  self.test_case_model_attention + "\n" + self.task_ge_testcase + "\n" + extracted_data["func_scenario"] + "\n" + self.attention_gen_testcase
        # prompt1 = self.role_prompt + "\n" + self.intro_gen_testcase + "\n" +self.scenario_model + "\n" + self.testcase_example + "\n" + \
        #           self.test_case_model_attention + "\n" + self.task_ge_testcase + "\n" + \
        #           self.ips + "\n" + self.attention_gen_testcase
        print("prompt1:", prompt1)
        response1 = request_response(prompt1)
        print("response1:", response1)
        parsed_response = json.loads(response1)
        result_content = parsed_response.get('choices', [{}]) [0].get('message', {}).get('content', '')
        testcase_str = self.get_code_block(result_content)
        print("code_block:", testcase_str)
        print("--------------------------------")
        testcase = self.parse_testcase_string(testcase_str)
        print("testcase:", testcase)
        print("---------------------------------")
        testcase = self.replace_ego(testcase, extracted_data["candidate_ego"])
        return testcase

    @staticmethod
    def get_code_block (response):
        try:
            # 1. 检测代码块并提取代码
            code_block_pattern = re.compile(r"```.*?\n(.*?)\n?```", re.DOTALL)
            matches = code_block_pattern.findall(response)  # 查找所有匹配的代码块
            if matches:
                # 只处理第一个匹配的代码块
                code = matches [0].strip()
                print("Extracted code block:", code)

                # 2. 提取第一个 `def testcase` 部分并去除注释
                testcase_pattern = re.compile(r"def\s+testcase\([^)]*\):", re.MULTILINE)
                match = testcase_pattern.search(code)
                if match:
                    # 找到第一个 `def testcase` 的起始位置
                    testcase_start = match.start()
                    # 找到第一个 `def testcase` 的结束位置（下一个 `def` 或文件结尾）
                    testcase_end = re.search(r"\ndef\s", code [testcase_start + 1:])
                    if testcase_end:
                        testcase_end = testcase_start + 1 + testcase_end.start()
                    else:
                        testcase_end = len(code)

                    testcase_code = code [testcase_start:testcase_end].strip()
                    print("Extracted testcase code:", testcase_code)

                    # 3. 去除注释
                    testcase_code_without_comments = re.sub(r"#.*", "", testcase_code)  # 删除单行注释
                    testcase_code_without_comments = re.sub(r'"""(.*?)"""', "", testcase_code_without_comments,
                                                            flags=re.DOTALL)  # 删除多行注释
                    testcase_code_without_comments = re.sub(r"'''(.*?)'''", "", testcase_code_without_comments,
                                                            flags=re.DOTALL)  # 删除多行注释
                    testcase_code_without_comments = re.sub(r'\n\s*\n', '\n', testcase_code_without_comments)  # 删除多余空行
                    return testcase_code_without_comments.strip()
                else:
                    return "No 'def testcase' found in the code block."
            else:
                return "No valid code block found in the content."
        except Exception as e:
            return f"Error occurred: {e}"

    @staticmethod
    def parse_testcase_string(testcase_str):
        testcase = TestCase()
        tree = ast.parse(testcase_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id == 'NPC':
                    assignee = node.targets[0].id
                    class_name = node.value.func.id
                    args = {}
                    arg_bounds = {}
                    for keyword in node.value.keywords:
                        if isinstance(keyword.value, ast.List):
                            try:
                                arg_bounds[keyword.arg] = [elt.n for elt in keyword.value.elts]
                                args[keyword.arg] = [elt.n for elt in keyword.value.elts]
                            except Exception as e:
                                arg_bounds[keyword.arg] = [1, 1]
                                args[keyword.arg] = [1, 1]
                        if isinstance(keyword.value, ast.Constant):
                            arg_bounds[keyword.arg] = keyword.value.value
                            args[keyword.arg] = keyword.value.value

                    statement = ConstructorStatement(testcase=testcase,
                                                     constructor_name=class_name,
                                                     assignee=assignee,
                                                     args=args,
                                                     arg_bounds=arg_bounds)
                    statement.update_ast_node()
                    testcase.add_statement(statement)

            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Attribute):
                    callee = node.value.func.value.id
                    method_name = node.value.func.attr
                    args = {}
                    arg_bounds = {}
                    for keyword in node.value.keywords:
                        if isinstance(keyword.value, ast.List):
                            arg_bounds[keyword.arg] = [elt.n for elt in keyword.value.elts]
                            args[keyword.arg] = [elt.n for elt in keyword.value.elts]
                        if isinstance(keyword.value, ast.Constant):
                            arg_bounds[keyword.arg] = keyword.value.value
                            args[keyword.arg] = keyword.value.value

                    statement = MethodStatement(testcase=testcase,
                                                callee=callee,
                                                method_name=method_name,
                                                args=args,
                                                arg_bounds=arg_bounds)
                    statement.update_ast_node()
                    testcase.add_statement(statement)

        print(astunparse.unparse(ast.fix_missing_locations(testcase.update_ast_node())))
        return testcase

    @staticmethod
    def replace_ego(testcase: TestCase, candidate_ego: list):
        # 选择主车，移除主车的动作
        statement_list = testcase.statements
        for i in reversed(range(len(statement_list))):
            statement = statement_list[i]
            if isinstance(statement, ConstructorStatement) and statement.assignee[-1] in candidate_ego:
                statement.assignee = 'ego'
                statement.update_ast_node()
                print("replace assignee")
            elif isinstance(statement, MethodStatement) and statement.callee[-1] in candidate_ego:
                testcase.remove_statement(statement)
                print("remove its action")

        print(astunparse.unparse(ast.fix_missing_locations(testcase.update_ast_node())))

        return testcase


if __name__ == '__main__':
    ips_to_testcase = IpsToTestcase()

    # file_path = r"C:\Users\Administrator\Desktop\test_gpt.json"

    # try:
    #     # 打开并读取 JSON 文件
    #     with open(file_path, "r", encoding="utf-8") as file:
    #         extracted_data = json.load(file)
    #
    #     # 打印读取的数据
    #     print("读取的 JSON 数据：")
    #     print(json.dumps(extracted_data, indent=4))
    #
    #     # 假设你有一个 IpsToTestcase 类，并且它有一个 convert 方法
    #     ips_to_testcase = IpsToTestcase()
    #     ips_to_testcase.convert(extracted_data)
    #
    # except FileNotFoundError:
    #     print(f"文件 {file_path} 未找到，请检查路径是否正确。")
    # except json.JSONDecodeError as e:
    #     print(f"解析 JSON 文件失败：{e}")
    # except Exception as e:
    #     print(f"发生错误：{e}")
    response = """```python\ndef testcase():\n  vehicle1 = NPC(lane_id=[2, 2], offset=[0.0, 0.0], initial_speed=[72.0, 72.0]) # V1 initial position and speed\n  vehicle2 = NPC(lane_id=[2, 2], offset=[-25.0, -25.0], initial_speed=[78.0, 78.0]) # V2 initial position and speed, behind V1\n  vehicle3 = NPC(lane_id=[3, 3], offset=[10.0, 10.0], initial_speed=[80.0, 80.0]) # V3 initial position and speed, parallel to V1\n  vehicle4 = NPC(lane_id=[1, 1], offset=[-30.0, -30.0], initial_speed=[70.0, 70.0]) # V4 initial position and speed, behind V1\n\n  # V1 decelerates abruptly\n  vehicle1.decelerate(target_speed=[30.0, 30.0], trigger_sequence=[1, 1]) \n\n  # V2 brake as V1 decelerates in front of it\n  vehicle2.decelerate(target_speed=[35.0, 35.0], trigger_sequence=[2, 2])\n\n  # V1 swerves left (change lane to lane 3)\n  vehicle1.changeLane(target_lane=[3, 3], target_speed=[70.0, 70.0], trigger_sequence=[3, 3])\n\n  # V3 continues straight ahead - no action needed as it's part of the initial setup.\n```"""
    ips_to_testcase = IpsToTestcase()
    code = ips_to_testcase.get_code_block(response)
    print(f"-------------------------{code}")
#     response = """
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
# {"id":"gen-1742733428-zuqOB0MIJaCBAYAIJBNQ","provider":"Chutes","model":"google/gemma-3-27b-it","object":"chat.completion","created":1742733428,"choices":[{"logprobs":null,"finish_reason":"stop","native_finish_reason":"stop","index":0,"message":{"role":"assistant","content":"\n```python\nclass NPC:\n    def __init__(self, lane_id: int, offset: float, initial_speed: float):\n        pass\n\n    def accelerate(self, target_speed: float, trigger_sequence: int):\n        pass\n\n    def decelerate(self, target_speed: float, trigger_sequence: int):\n        pass\n\n    def changeLane(self, target_lane: int, target_speed: float, trigger_sequence: int):\n        pass\ndef testcase(): \n  vehicle1 = NPC(lane_id=1, offset=[50.0, 100.0], initial_speed=[75.0, 75.0])  # V1 initial position and speed\n  vehicle2 = NPC(lane_id=1, offset=[20.0, 30.0], initial_speed=[75.0, 75.0])  # V2 initial position and speed\n  vehicle3 = NPC(lane_id=2, offset=[50.0, 100.0], initial_speed=[70.0, 70.0])  # V3 initial position and speed\n\n  vehicle2.decelerate(target_speed=[30.0, 40.0], trigger_sequence=1) # V2 decelerates due to congestion\n  vehicle3.decelerate(target_speed=[20.0, 30.0], trigger_sequence=1) # V3 decelerates due to congestion\n\n  vehicle1.decelerate(target_speed=[60.0, 65.0], trigger_sequence=2) #V1 starts to brake as it approaches V2\n  vehicle1.changeLane(target_lane=2, target_speed=[60.0, 65.0], trigger_sequence=3) # V1 swerves right to avoid V2\n  vehicle1.changeLane(target_lane=1, target_speed=[50.0, 60.0], trigger_sequence=4) #V1 swerves left, impacting V2\n\n  vehicle3.decelerate(target_speed=[10.0, 15.0], trigger_sequence=5) #V3 brakes further as V1 enters its lane\n  vehicle1.changeLane(target_lane=2, target_speed=[20.0, 30.0], trigger_sequence=6) # V1 continues moving towards the right\n  vehicle3.decelerate(target_speed=[5.0, 10.0], trigger_sequence=7) #V3 brakes to avoid collision\n```","refusal":null}}],"usage":{"prompt_tokens":798,"completion_tokens":593,"total_tokens":1391}}"""
#     testcase_str = ips_to_testcase.get_code_block(response)
#     print("code_block:", testcase_str)
#     testcase_str ="""
# {
#     "choices": [
#         {
#             "message": {
#                 "content": "\\n```python\\ndef testcase(self):\\n        vehicle1 = NPC(lane_id=[4, 4], offset=[50.0, 100.0], initial_speed=[105.0, 105.0])\\n        vehicle2 = NPC(lane_id=[5, 5], offset=[0.0, 50.0], initial_speed=[105.0, 105.0])\\n        vehicle3 = NPC(lane_id=[3, 3], offset=[50.0, 100.0], initial_speed=[105.0, 105.0])\\n        vehicle3.changeLane(target_lane=[4, 4], target_speed=[105.0, 105.0], trigger_sequence=[1, 1]) \\n        vehicle1.decelerate(target_speed=[90.0, 95.0], trigger_sequence=[2, 2]) \\n        vehicle1.changeLane(target_lane=[5, 5], target_speed=[100.0, 105.0], trigger_sequence=[3, 3]) \\n        vehicle1.changeLane(target_lane=[5, 5], target_speed=[105.0, 105.0], trigger_sequence=[4, 4]) \\ndef testcase(): \\n  vehicle1 = NPC(lane_id=[4, 4], offset=[50.0, 100.0], initial_speed=[105.0, 105.0]) \\n  vehicle2 = NPC(lane_id=[5, 5], offset=[0.0, 50.0], initial_speed=[105.0, 105.0]) \\n  vehicle3 = NPC(lane_id=[3, 3], offset=[50.0, 100.0], initial_speed=[105.0, 105.0])\\n  vehicle3.changeLane(target_lane=[4, 4], target_speed=[105.0, 105.0], trigger_sequence=[1, 1]) \\n  vehicle1.decelerate(target_speed=[90.0, 95.0], trigger_sequence=[2, 2]) \\n  vehicle1.changeLane(target_lane=[5, 5], target_speed=[100.0, 105.0], trigger_sequence=[3, 3]) \\n  vehicle1.changeLane(target_lane=[5, 5], target_speed=[105.0, 105.0], trigger_sequence=[4, 4])\\n```"
#             }
#         }
#     ]
# }
# """
#
#     testcase = ips_to_testcase.get_code_block(testcase_str)
#     print("代码块:",testcase)

    end_time = time.time()
    run_time = end_time - start_time
    print(f"代码运行总时间: {run_time} 秒")
