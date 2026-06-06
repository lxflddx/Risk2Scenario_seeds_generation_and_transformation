import requests
import json
import time

# gemma api key
OPENROUTER_API_KEY = 'sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

URL = "https://openrouter.ai/api/v1/chat/completions"
# deepseek/deepseek-chat-v3-0324:free   qwen/qwen2.5-vl-3b-instruct:free   google/gemma-3-27b-it:free
# deepseek/deepseek-r1-zero:free        qwen/qwen3-32b:free
start_time = time.time()
def request_response(content):
    """
    调用 LLM API 并获取响应
    :param content: 用户输入的内容
    :return: API 返回的响应文本，或者 None（如果发生错误）
    """
    while True:
        try:
            response = requests.post(
                url=URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                },
                data=json.dumps({
                    "model": "google/gemma-3-27b-it",  # Optional
                    "messages": [
                        {"role": "user", "content": content}
                    ],
                    "top_p": 1,
                    "temperature": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                    "repetition_penalty": 1,
                    "top_k": 0,
                })
            )
            # 检查请求是否成功
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
            elif response_status_code == 429:  # 请求过多
                print("Rate limit exceeded. Retrying after 20 seconds...")
                time.sleep(20)
            else:
                print(f"Error: {response.status_code}, {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}. Retrying in 15 seconds...")
            time.sleep(30)

# content ="""You are an accident analysis expert with extensive knowledge in the traffic field. Please follow these steps to complete the task, and do not output in markdown format:
# 1. Summarize the Accident Report:
#   ○ Please read and summarize the following accident report, highlighting the basic situation and key information.
# 1. Analyze Risk Factors:
#   ○ Extract key information from the accident report and consider all risk factors, both direct and potential, that could have contributed to the accident.
#   ○ Please explain how each risk factor may have played a role in the accident, either through direct causation or by creating conditions that increased the likelihood of the accident occurring..
# 2. Categorize Risk Factors by Layer:
#   ○ Please categorize the risk factors that contributed to the accident according to the following scenario layers and output as a JSON format object.
#   [JSON] - Please include this marker at the beginning of your output.
# {
#   "risk_factor_classification": {
#     "Road Layer": [...],
#     "Infrastructure Layer": [...],
#     "Object Interaction Layer": [...],
#     "Weather Layer": [...]
#   }
# }
# [/JSON] - Please include this marker at the end of your output.
#   ○ The object should contain a key for risk factor hierarchical classification, whose value is a hierarchical list of risk factors. .
#   ○ Each risk factor should include two fields: 'Risk Factor' and 'Specific Description'. If the factor did not directly or potentially contribute to the accident, then it should not be included in the JSON.
#
# summary:
# This crash occurred at a T-intersection_gemma of two undivided roadways. The east/west roadway had four lanes of travel (two in each direction) and the north/south roadway had two lanes of travel (one in each direction). The southbound roadway ended at the T-intersection_gemma and was controlled by a stop sign. The east/west roadway had no traffic control device. The conditions were as follows: early evening, partly cloudy skies, the roadway was dry and there were no adverse atmospheric conditions.  The gradient for southbound traffic was +4 percent. The westbound roadway at the intersection_gemma was level. The posted speed limit on the north/south roadway was 40 kmph (25 mph).  The posted speed limit on the east/west roadway was 72 kmph (45 mph).
#
# V1, a 2005 Chevrolet Malibu, was driven by a 38-year old male. V1 was initially traveling southbound, and was intending to turn left at the T-intersection_gemma to head eastbound.  V2, a 2004 Chrysler Pacifica, was driven by a 39-year old female who was traveling westbound. Traffic was backed-up in the first westbound lane and had come to a stop. Traffic in the second westbound lane was still moving. V2 was traveling in lane two. A non-contact box truck that was stopped in the first westbound lane waved out V1 from its stop sign. As V1 pulled across the second westbound lane, the left front of V1 struck the left front of V2.
#
# There was no driver interview obtained for V1 after numerous times of trying to contact the driver.  V1 needed to be towed due to damage.  The police report did not indicate any injuries or the involvement of drugs or alcohol.   The police reported V1 traveling at an unknown speed.
#
# The Critical Pre-crash Event for V1 was coded as this vehicle turning left at intersection_gemma.  The Critical Reason for the Critical Pre-crash Event was coded as an "other" decision error - turned with obstructed view. The non-contact vehicle was coded as a sightline restriction. Other associated factors coded to this driver include inadequate surveillance and a traffic flow interruption caused by rush hour congestion.
#
# There was no driver interview obtained for V2 after numerous times of trying to contact the driver.  V2 needed to be towed due to damage.  The police report did not indicate any injuries or the involvement of drugs or alcohol.   The police reported V2 traveling at an unknown speed.
#
# The Critical Pre-crash Event for V2 was coded as other vehicle encroachment from crossing street, turning into opposite direction.  The Critical Reason for the Critical Pre-crash Event was not coded to this vehicle. Associated factors coded to this driver include an "other" recognition error in that the impending problem was masked by the traffic flow pattern, a sightline restriction caused by the non-contact truck in the right lane, and the traffic flow interruption caused by rush hour congestion.
#
#
# Scenario Layering:
# 1. Road Layer:
#   ○ Road materials and types
#   ○ Road conditions (such as slope, surface condition, etc.)
#   ○ Intersection design (including the topology of the roads)
# 2. Infrastructure Layer:
#   ○ Traffic signals
#   ○ Traffic signs
#   ○ Other traffic control facilities
# 3. Object Interaction Layer:
#   ○ Driver behavior
#   ○ Vehicles (including types, speeds, paths, etc.)
#   ○ Traffic conditions (such as congestion)2036#   95-1*#   ○ Visibility obstructions (caused by other vehicles, obstacles, etc.)
# 4. Weather Layer:
#   ○ Rain or snow
#   ○ Wind
#   ○ Fog
#   ○ Other weather conditions that may affect traffic
# ● Explanation: This hierarchical structure is exemplary in nature and is intended to provide a basic framework. In practical applications, the hierarchical structure can be adjusted and expanded according to specific needs and contexts. If risks not explicitly listed in the current hierarchy are encountered, they can be added to the most appropriate layer or subclass, or new layers or subclasses can be created if necessary.
# """

# if __name__ == '__main__':
#
#     content =""""""
#     response = request_response(content)
#     end_time = time.time()
#     print("time:", end_time - start_time)
#     print(response)
