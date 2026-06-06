import json
import re
import traceback
import time

from risk2scenario.utils.llm_util import request_response


start_time = time.time()


class ExtractTAS:

    def __init__(self):

        self.prompt = """
You are an autonomous driving scenario modeling expert.

Your task is to convert a natural-language traffic accident scenario description into a structured Temporal Action Sequence (TAS) scenario representation.

The conversion process should follow the Temporal Action Sequence extraction methodology.

--------------------------------------------------
# Extraction Procedure

## Step 1: Environmental Context Extraction

Extract the static environmental context information from the scenario description.

The environmental context should include:
- time information
- weather condition
- road surface condition
- road type
- road geometry
- lane structure
- traffic infrastructure (if mentioned)

--------------------------------------------------
## Step 2: Traffic Participant Initial State Extraction

Identify all traffic participants in the scenario.

Assign a unique numeric identifier to each vehicle:

- V1
- V2
- V3
...

Do NOT use alphabetic identifiers.

For each vehicle, extract:
- vehicle type (if mentioned)
- initial lane position
- initial motion state
- relative longitudinal position – specify the vehicle's front/back relationship with respect to other vehicles in the same lane or adjacent lanes (e.g., "V1 is 20 m ahead of V2", "V3 is 10 m behind V4", or "V2 is the leading vehicle in lane 1", "V5 follows V1 in the same lane")
--------------------------------------------------
# Lane ID Definition

Lane IDs increase from right to left.

- rightmost lane = lane 1
- second rightmost lane = lane 2
- continue increasing toward the left

--------------------------------------------------
## Step 3: Relation Triple Extraction

Treat Temporal Action Sequence extraction as a relation extraction task.

First extract relation triples internally.

Relation format:

(subject, relation, object)

--------------------------------------------------
# Predefined Relation Types

## Spatial Relations

(Vehicle, Located, Roadtype)

(Vehicle, Located, Lane)

--------------------------------------------------
## Action Relations

(Vehicle, accelerate, None/Lane/Roadtype)

(Vehicle, decelerate, None/Lane/Roadtype)

(Vehicle, keep_speed, None/Lane/Roadtype)

(Vehicle, lane_change_left, TargetLane)

(Vehicle, lane_change_right, TargetLane)

(Vehicle, strike, Vehicle)

--------------------------------------------------
## Step 4: Temporal Action Sequence Construction

Based on the extracted relation triples:

1. Organize the vehicle interactions chronologically.

2. Construct a Temporal Action Sequence (TAS).

Each temporal action unit must follow this format:

[
  subject,
  action,
  direction,
  road_type,
  lane,
  target_object,
  time_step
]

--------------------------------------------------
# Temporal Constraints

- Preserve the original temporal order.
- Use discrete temporal labels:
"1", "2", "3", ...
----------------------------------------------------
## Step 5: Candidate Ego Vehicle Selection
Select the vehicle that does NOT perform the immediate conflict-inducing action (e.g., sudden deceleration, lane change) from the two vehicles involved in the first collision. This vehicle will be the ego.

Output the result as:

"Candidate Ego Vehicle": "Vx"

where Vx is the selected vehicle identifier.

--------------------------------------------------
# Output Format

Output ONLY one valid JSON object.

Wrap the JSON between:

###BEGIN_JSON###
and
###END_JSON###

JSON format:

###BEGIN_JSON###
{
  "Environmental Context": "",

  "Agent Initial States": [
    ""
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
    ]
  ],
   "Candidate Ego Vehicle": "Vx"

}
###END_JSON###

--------------------------------------------------
# Constraints

- Do not output explanations.
- Do not output markdown.
- Do not output intermediate relation triples.
- Preserve temporal consistency.
- Use only predefined action types.
- Output valid JSON only.
"""

    def extract(self, description):

        final_prompt = self.prompt + "\n\nScenario Description:\n" + description

        print("prompt:\n", final_prompt)

        response = request_response(final_prompt)

        print("response:\n", response)

        tas_json = self.extract_json(response)

        print("tas_json:\n", tas_json)

        return tas_json

    @staticmethod
    def extract_json(response):

        try:

            if response is None:
                print("Error: response is None")
                return None

            # OpenAI格式
            if isinstance(response, dict):

                content = response.get(
                    'choices',
                    [{}]
                )[0].get(
                    'message',
                    {}
                ).get(
                    'content',
                    ''
                )

            else:

                try:
                    response_dict = json.loads(response)

                    content = response_dict.get(
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
                    content = response

            print("content:\n", content)

            # 提取JSON块
            match = re.search(
                r"###BEGIN_JSON###(.*?)###END_JSON###",
                content,
                re.DOTALL
            )

            if not match:
                print("Error: JSON markers not found")
                return None

            json_text = match.group(1).strip()

            print("json_text:\n", json_text)

            tas_json = json.loads(json_text)

            return tas_json

        except Exception as e:

            print("error:", e)

            traceback.print_exc()

            return None


if __name__ == '__main__':

    extractor = ExtractTAS()

    description = """
Vehicle 1 (V1) is traveling eastbound in lane 1, positioned 20 meters behind a large truck (T1) that obstructs its view. Due to T1's slow speed and heavy traffic congestion, V1 decides to overtake by moving into lane 2, which is initially free. However, upon encountering more traffic in lane 2, V1 attempts to change lanes into lane 3, where it misjudges the gap and collides with Vehicle 2 (V2). V2, which was waiting in the center turn lane, had started a left turn into the eastbound lanes, finding a gap in westbound traffic. The collision between V1 and V2 in lane 3 causes traffic to halt and leads to secondary congestion issues."""

    result = extractor.extract(description)

    print("\nFinal Result:\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    end_time = time.time()

    print(f"\nRuntime: {end_time - start_time} seconds")