# coding: utf-8
import re

import markdown
import json
import time
import pandas as pd
from bs4 import BeautifulSoup

from risk2scenario.utils.llm_util import request_response
from risk2scenario.search.search_query_risks import search_risk, load_risk_data_and_model

OPENROUTER_API_KEY = 'your key'

url = "https://openrouter.ai/api/v1/chat/completions"
start_time = time.time()


def markdown_to_plain_text(md_text):
    html = markdown.markdown(md_text)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()


class GenerateDiscription:
    def __init__(self):
        self.role_prompt = ("You are a traffic scenario generation expert tasked with creating concise and realistic "
                            "descriptions of hazardous traffic situations involving multiple vehicles on straight "
                            "roads. Your goal is to use the provided Basic Scenario and Risk Factors to create two "
                            "different scenarios that are logically consistent, complex, and realistic multi-vehicle "
                            "traffic hazard.\n")
        self.task_summarize_prompt = (
            "Task Structure:\n"
            "Step 1: Risk Factor Interpretation\n"
            "For each Risk Factor provided, explain:\n"
            "- What it means in general terms.\n"
            "- How this risk manifests as a vehicle behavior pattern (e.g., encroachment = drifting over lane lines "
            "during lane change).\n "
            "- What physical or environmental conditions might make this risk more likely\n"
            "Step 2: Scenario Foundation\n"
            "Understand and restate the Basic Scenario clearly.\n"
            "Break it down into:\n"
            "- The initial road layout and weather or road conditions.\n"
            "- The involved vehicles and their maneuvers before the incident.\n"
            "- Which vehicle initiates the hazard and which are vulnerable participants.\n"
            "Step 3: Risk Integration and Scenario Expansion (One by One)\n"
            "Add one Risk Factor at a time to the scenario, and with each:\n"
            "- Adjust the positions, intents, or reactions of the vehicles accordingly.\n"
            "- Ensure that the behavior change is physically realistic and logically connected to the prior events.\n"
            "Step 4: Final Scenario Composition\n"
            "Generate a coherent and plausible paragraph describing the entire sequence of events from vehicle "
            "initialization to hazardous outcome. Follow this output format:\n "
            "Vehicle Initialization:\nList all involved vehicles (V1, V2, V3, etc.). For each, provide:\n"
            "- Lane assignment (Lane 1 = rightmost).\n- Relative position (e.g., “V1 is 15 meters ahead of V2”).\n- "
            "Intent (e.g., slowing to merge, cruising, overtaking)\n"
            "Scenario Development:\nDescribe the chain of events that led to the hazard:\n- Begin from initial motion states\n- Gradually introduce each risk factor into the scenario logic\n- Focus on how each risk altered vehicle behavior\n- Emphasize interactions between multiple vehicles (at least two), including evasive actions or secondary impacts.\n"
            "Outcome:\nConclude with the final result (collision, near-miss, pile-up, traffic blockage), specifying which vehicles were involved and how.\n"
        )
        self.constrain_prompt = (
            "Constraints:\n- Every vehicle in the description must be introduced in the Vehicle Initialization section\n- Each risk factor must appear in the scenario logic\n- Use three or more vehicles when possible, to increase interaction complexity\n- Scenario must be on a straight road with no intersections\n- All events must be realistic and physically plausible\n- The road has up to five lanes, numbered from right to left (Lane 1 is the rightmost lane)\n")
        # with open('D:\\pythonProject\\LLM_Scenario\search\\basic_scenario_description.txt', 'r') as f:
        #     self.query = f.read()
        with open('/risk2scenario/search\\current_risk.txt', 'r', encoding='utf-8') as f:
            self.current_risk = f.read()

    def generate_description(self, query_risk):
        prompt = self.role_prompt + self.task_summarize_prompt + self.constrain_prompt + "Basic Scenario:\n" + query_risk + "\n" + "Risk Factors:\n" + self.current_risk
        print(prompt)
        response = request_response(prompt)
        print("response:", response)
        scenarios = self.extract_description(response)
        return scenarios
        # func_scenario, func_scenario_dict, candidate_ego = self.extract_scenario_dict(response)
        # extracted_data = {"func_scenario": func_scenario, "func_scenario_dict": func_scenario_dict, "candidate_ego": random.choice(candidate_ego)}  # 字典，包含功能场景、功能场景字典、候选ego
        # print("extracted_data:", extracted_data)
        # return extracted_data
        # 怎么处理后面再说，选定了模型之后再说

    def extract_description(self, response):
        lines = response.strip().splitlines()
        cleaned_content = "\n".join(lines).replace("\n", "\\n").replace("\t", "\\t")
        json_data = json.loads(cleaned_content)
        content = json_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print("content:\n", content, "\n")
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, "html.parser")
        content = soup.get_text()
        # pattern = re.compile(r"Scenario \d+:[\s\S]+?(?=Scenario \d+|$)", re.DOTALL)
        # pattern = re.compile(r"Vehicle Initialization:.*?Outcome:.*?(?=Vehicle Initialization:|###|$)", re.DOTALL)
        pattern = re.compile(r"Vehicle Initialization:.*?Outcome:.*?(?=Scenario \d+|$)", re.DOTALL)

        scenarios = pattern.findall(content)
        return scenarios


    @staticmethod
    def save_to_excel(scenarios, output_file):
        df = pd.DataFrame({
            "ID": [1],
            "Scenario_Description": [scenarios]
        })
        df.to_excel(output_file, index=False)
        print("保存成功！")


if __name__ == '__main__':
    file_path = 'D:\\pythonProject\\LLM_Scenario\\new_risk_json\\unique_risk_factors.json'
    load_risk_data_and_model(file_path)
    # 查询风险
    query_risk = "A car drifted out of its lane during a lane change, sideswiping a truck in the adjacent lane."
    search_risk(query_risk)
    generator = GenerateDiscription()
    scenarios = generator.generate_description(query_risk)
    for i, scenario in enumerate(scenarios, start=1):
        scenario_without_newlines = scenario.replace("\n", "")
        print(f"### 场景 {i}：")
        print(scenario_without_newlines.strip())
        print("\n")
    # generator.extract_description(response)
    end_time = time.time()
    run_time = end_time - start_time
    print(f"代码运行总时间: {run_time} 秒")
#A vehicle stopped to make a left turn was rear-ended by another vehicle traveling in the same direction, due to the following driver's distraction.
# A vehicle lost control while avoiding a lane-changing car, collided with another vehicle, and then hit the barrier wall.
# A car overtaking another vehicle drifted into the adjacent lane and sideswiped a third vehicle.
# A car drifted out of its lane during a lane change, sideswiping a truck in the adjacent lane.
# A car drifted out of its lane during a lane change, sideswiping a truck in the adjacent lane.