import json
import re
import traceback
import time

from risk2scenario.utils.llm_util import request_response


start_time = time.time()


class TASToLogicalScenario:

    def __init__(self):

        self.prompt = """
You are an autonomous driving scenario modeling expert.

Your task is to convert a Temporal Action Sequence (TAS) scenario representation into a structured logical scenario JSON configuration, using the ego vehicle selected in the previous step.

==================================================

Logical Scenario Mapping Procedure
Step 1: Static Environment Mapping

Map the environmental context into the world module.

Allowed parameters:

world.time_of_day:

daytime
night

world.weather:

clear
cloudy
rain
snow

world.road_condition:

dry
slippery

==================================================

Step 2: Road Structure Mapping

road.structure.type:

roadway

road.structure.layout:

straight
curve

road.structure.num_lanes:

integer between 1 and 4

road.structure.slope:

uphill
downhill
flat

road.infrastructure.roadside_safety:

wide_shoulder
rigid_barrier

==================================================

Step 3: Lane ID Definition

Lane IDs increase from right to left.

rightmost lane = lane 1
second rightmost lane = lane 2

Additionally, for vehicle longitudinal positioning: a larger offset value indicates the vehicle is further ahead (more forward) along the lane.
==================================================
Step 4: Vehicle Initialization

Convert all traffic participants into vehicle objects using **only the first time step of the TAS** (where all vehicles have "keep_speed").

Each vehicle object must contain:
  vehicle_id
  lane_id
  offset
  initial_speed

All numeric parameters must use ranges: [min, max]

**Rules (must follow):**
- `lane_id`: Copy directly from the TAS field "lane" (e.g., "lane 1" → [1,1]; "lane 2" → [2,2]).
- `initial_speed`: Copy from the TAS speed value (if given as a single number, convert to [value-5, value+5] or similar plausible range).
- `offset`: Assign based on **relative longitudinal order** inferred from the TAS description and the action sequence.  
  - **Larger offset = further ahead.**  
  - For example: if V1 is described as "behind V2", then offset_V1 < offset_V2.  
  - If no explicit order is given, assume all vehicles in the same lane are offset according to their position in the TAS list (first vehicle = most ahead).
- Do NOT generate any action for "keep_speed" in Step 5.

==================================================

Step 5: Temporal Action Sequence Mapping

Allowed action types:
Accelerate
Decelerate
LaneChanging
Collision

Action parameters:
Accelerate / Decelerate:
  target_speed
  trigger_sequence
  time_interval

LaneChanging:
  target_lane
  target_speed
  trigger_sequence
  time_interval

Collision:
  target_vehicle
  trigger_sequence
  time_interval

Trigger rules:
- actions with same trigger_sequence occur simultaneously
- maximum trigger_sequence <= 5

Time interval rules:
- time_interval represents relative delay
- actions with same trigger_sequence MUST share identical time_interval

**Mapping rules (strict order):**
1. Ignore **all** "keep_speed" actions (they are already used for initialization).
2. Collect all **remaining TAS time steps** (those with actual actions like lane_change, decelerate, accelerate, strike).
3. Preserve their **temporal order**.
4. Map these time steps to `trigger_sequence` values from 1 to 5 as follows:
   - Assign the earliest remaining step to `trigger_sequence = 1`.
   - If there are more than 5 steps, **group consecutive steps** into the same `trigger_sequence` (e.g., steps 1–2 → seq 1, steps 3–4 → seq 2, steps 5–6 → seq 3, steps 7–8 → seq 4, steps 9–10 → seq 5).  
   - **Never reorder steps**; a later step cannot have a smaller `trigger_sequence` than an earlier step.
5. Action type mapping:
   - `lane_change_left` / `lane_change_right` → `LaneChanging` (set `target_lane` to the destination lane number)
   - `decelerate` → `Decelerate`
   - `accelerate` → `Accelerate`
   - `strike` with a vehicle ID → `Collision` with `target_vehicle` = that ID
   - `strike` with "barrier" → `Collision` with `target_vehicle` = "barrier"
6. For `LaneChanging` actions, also include `target_speed` (can use a range based on the speed at that time).
==================================================

Step 6: Use Preselected Ego Vehicle
Use the ego vehicle ID selected from the previous step.
Do not perform any additional selection; replace placeholder ego vehicle with the preselected ID in the JSON if needed.

==================================================

Output Format

Output ONLY the logical scenario JSON. Do not output explanations.

==================================================

JSON Template
Output ONLY one valid JSON object.

Wrap the JSON between:

###BEGIN_JSON###
and
###END_JSON###

JSON format:

###BEGIN_JSON###
{
"world": {
"time_of_day": "",
"weather": "",
"road_condition": ""
},

"road": {
"structure": {
"type": "roadway",
"layout": "",
"num_lanes": 0,
"slope": ""
},

"infrastructure": {  
  "roadside_safety": ""  
}  

},

"vehicles": [
{
"vehicle_id": "V1",
"lane_id": [1,1],
"offset": [40,50],
"initial_speed": [20,30]
}
],

"actions": [
{
"vehicle_id": "V1",
"type": "Decelerate",
"target_speed": [20,30],
"trigger_sequence": [1,1],
"time_interval": [1,2]
},

{  
  "vehicle_id": "V1",  
  "type": "Collision",  
  "target_vehicle": "V2",  
  "trigger_sequence": [3,3],  
  "time_interval": [1,2]  
}  

]
}
###END_JSON###
"""


    def convert(self, tas_json):

        input_text = json.dumps(
            tas_json,
            indent=2,
            ensure_ascii=False
        )

        final_prompt = self.prompt + "\n\nInput TAS Scenario:\n" + input_text

        print("prompt:\n", final_prompt)

        response = request_response(final_prompt)

        print("response:\n", response)

        content = self.extract_content(response)

        logical_json = self.extract_json(content)

        ego_vehicle_id = tas_json.get("Candidate Ego Vehicle")

        if ego_vehicle_id:
            print("start repalce")
            logical_json = self.replace_ego(logical_json, ego_vehicle_id)

        print("final logical scenario:\n", logical_json)
        return logical_json


    @staticmethod
    def extract_content(response):

        if response is None:
            return ""

        if isinstance(response, dict):

            return response.get(
                'choices',
                [{}]
            )[0].get(
                'message',
                {}
            ).get(
                'content',
                ''
            )

        try:

            response_dict = json.loads(response)

            return response_dict.get(
                'choices',
                [{}]
            )[0].get(
                'message',
                {}
            ).get(
                'content',
                ''
            )

        except:

            return response

    @staticmethod
    def extract_json(content):

        try:

            match = re.search(
                r"###BEGIN_JSON###(.*?)###END_JSON###",
                content,
                re.DOTALL
            )

            if not match:

                print("json not found")

                return None

            json_text = match.group(1).strip()

            print("json_text:\n", json_text)

            logical_json = json.loads(json_text)

            return logical_json

        except Exception as e:

            print(e)

            traceback.print_exc()

            return None

    @staticmethod
    def replace_ego (logical_json, ego_vehicle_id):
        try:
            if logical_json is None:
                return None

            # ==================================================
            # replace vehicle id with "ego"
            # ==================================================
            for vehicle in logical_json.get("vehicles", []):
                if vehicle ["vehicle_id"] == ego_vehicle_id:
                    vehicle ["vehicle_id"] = "ego"
            print("replaced")

            # ==================================================
            # optionally remove ego's actions if needed
            # ==================================================
            new_actions = []
            for action in logical_json.get("actions", []):
                if action ["vehicle_id"] == ego_vehicle_id:
                    continue
                if action ["type"].lower() in ["strike", "collision"]:
                    continue
                new_actions.append(action)

            logical_json ["actions"] = new_actions
            return logical_json

        except Exception as e:
            import traceback
            print(e)
            traceback.print_exc()
            return logical_json


if __name__ == '__main__':

    converter = TASToLogicalScenario()

    tas_json = {
  "Environmental Context": "Multi-lane highway, daylight, dry road conditions.",
  "Agent Initial States": [
    "V1: Vehicle, Lane 2, keep_speed",
    "V2: Vehicle, Lane 1, keep_speed",
    "V3: Vehicle, Lane 3, keep_speed",
    "V4: Vehicle, Lane 2, keep_speed"
  ],
  "Temporal Action Sequence": [
    [
      "V1",
      "keep_speed",
      "east",
      "eastbound",
      "lane 2",
      "",
      "1"
    ],
    [
      "V2",
      "keep_speed",
      "east",
      "eastbound",
      "lane 1",
      "",
      "1"
    ],
    [
      "V3",
      "lane_change_left",
      "east",
      "eastbound",
      "lane 3",
      "lane 2",
      "2"
    ],
    [
      "V4",
      "decelerate",
      "east",
      "eastbound",
      "lane 2",
      "",
      "3"
    ],
    [
      "V1",
      "decelerate",
      "east",
      "eastbound",
      "lane 2",
      "",
      "3"
    ],
    [
      "V1",
      "lane_change_right",
      "east",
      "eastbound",
      "lane 2",
      "lane 1",
      "4"
    ],
    [
      "V2",
      "decelerate",
      "east",
      "eastbound",
      "lane 1",
      "",
      "5"
    ],
    [
      "V1",
      "strike",
      "east",
      "eastbound",
      "lane 1",
      "V2",
      "6"
    ],
    [
      "V1",
      "strike",
      "east",
      "eastbound",
      "lane 1",
      "barrier",
      "7"
    ]
  ],
  "Candidate Ego Vehicle": "V2"
}

    result = converter.convert(tas_json)

    print("\n================ FINAL RESULT ================\n")

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )

    end_time = time.time()

    print(f"\nRuntime: {end_time - start_time} seconds")