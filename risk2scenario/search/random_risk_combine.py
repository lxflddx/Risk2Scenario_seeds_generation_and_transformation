import random
from typing import Dict, List, Tuple
"""
随机采样
"""

# 所有风险因素维度及其可选水平
INPUT_MAPPING = {
    'RoadCurvature': ['Straight', 'Curve'],
    'RoadGrade': ['Flat', 'Downhill', 'Uphill'],
    'LaneConfiguration': ['DividedLanes', 'UndividedLanes'],
    'RoadsideSafetyZone': ['WideShoulder', 'RigidObstacle'],
    'FollowingBehavior': ['SafeFollowing', 'FollowingTooClosely'],
    'SpeedInteraction': ['SpeedCoordination', 'LargeSpeedDifference'],
    'KeyVehicleBehavior': ['NormalDriving', 'EmergencyBraking', 'IllegalCutIn', 'IllegalEvasion'],
    'RoadFrictionCoefficient': ['Dry', 'Slippery'],
    'VisibilityConditions': ['Good', 'Nighttime', 'AdverseWeather']
}


def is_valid_combination(combo: Dict[str, str]) -> bool:
    """
    检查一个标签组合是否满足约束条件
    """
    # 约束1:
    # if [VisibilityConditions] = "AdverseWeather"
    # then [RoadFrictionCoefficient] <> "Dry"
    if combo['VisibilityConditions'] == 'AdverseWeather' and combo['RoadFrictionCoefficient'] == 'Dry':
        return False

    # 约束2:
    # if [FollowingBehavior] = "FollowingTooClosely"
    # then [SpeedInteraction] <> "SpeedCoordination"
    if combo['FollowingBehavior'] == 'FollowingTooClosely' and combo['SpeedInteraction'] == 'SpeedCoordination':
        return False

    # 约束3:
    # if [RoadCurvature] = "Curve"
    # then [RoadGrade] = "Flat"
    if combo['RoadCurvature'] == 'Curve' and combo['RoadGrade'] != 'Flat':
        return False

    return True


def combo_to_tuple(combo: Dict[str, str], keys: List[str]) -> Tuple[str, ...]:
    """
    将组合转成可哈希的tuple，便于判重
    """
    return tuple(combo[k] for k in keys)


def generate_random_valid_combo(rng: random.Random) -> Dict[str, str]:
    """
    随机生成一个合法组合
    """
    while True:
        combo = {
            factor: rng.choice(levels)
            for factor, levels in INPUT_MAPPING.items()
        }
        if is_valid_combination(combo):
            return combo


def generate_random_unique_combos(
    n: int = 14,
    seed: int = 42,
    max_attempts: int = 10000
) -> List[Dict[str, str]]:
    """
    随机生成 n 个合法且不重复的标签组合
    """
    rng = random.Random(seed)
    keys = list(INPUT_MAPPING.keys())

    results: List[Dict[str, str]] = []
    seen = set()
    attempts = 0

    while len(results) < n:
        attempts += 1
        if attempts > max_attempts:
            raise RuntimeError(
                f"无法在 {max_attempts} 次尝试内生成 {n} 个合法且不重复的组合，请检查约束是否过严。"
            )

        combo = generate_random_valid_combo(rng)
        combo_key = combo_to_tuple(combo, keys)

        if combo_key not in seen:
            seen.add(combo_key)
            results.append(combo)

    return results


def combos_to_tab_strings(combos: List[Dict[str, str]]) -> List[str]:
    """
    将组合转成制表符分隔字符串，顺序与你 parse_input_string 对应
    """
    keys = list(INPUT_MAPPING.keys())
    lines = []
    for combo in combos:
        line = '\t'.join(combo[k] for k in keys)
        lines.append(line)
    return lines


def print_combos(combos: List[Dict[str, str]]) -> None:
    """
    打印组合，便于查看
    """
    for idx, combo in enumerate(combos, start=1):
        print(f"Combination {idx}:")
        for k, v in combo.items():
            print(f"  {k}: {v}")
        print("-" * 50)


if __name__ == "__main__":
    random_combos = generate_random_unique_combos(n=14, seed=2026)

    print("=== Random Valid Unique Combinations ===")
    print_combos(random_combos)

    print("\n=== Tab-separated format ===")
    tab_lines = combos_to_tab_strings(random_combos)
    for line in tab_lines:
        print(line)