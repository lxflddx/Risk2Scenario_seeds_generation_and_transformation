import itertools
from typing import List, Dict
from random_risk_combine import generate_random_unique_combos, INPUT_MAPPING, is_valid_combination
"""
随机采样并计算覆盖
"""

def generate_all_valid_combos() -> List[Dict[str, str]]:
    """
    枚举所有满足约束的合法标签组合
    """
    keys = list(INPUT_MAPPING.keys())
    all_values = [INPUT_MAPPING[k] for k in keys]

    valid_combos = []
    for values in itertools.product(*all_values):
        combo = dict(zip(keys, values))
        if is_valid_combination(combo):
            valid_combos.append(combo)

    return valid_combos


def extract_pairs_from_combo(combo: Dict[str, str]) -> set:
    """
    提取一个组合中包含的所有 pair
    pair 的表示形式为:
    ((factor1, level1), (factor2, level2))
    """
    items = list(combo.items())
    pairs = set()

    for (f1, v1), (f2, v2) in itertools.combinations(items, 2):
        # 保证顺序一致，便于比较
        if f1 < f2:
            pair = ((f1, v1), (f2, v2))
        else:
            pair = ((f2, v2), (f1, v1))
        pairs.add(pair)

    return pairs


def get_all_valid_pairs(valid_combos: List[Dict[str, str]]) -> set:
    """
    从所有合法组合中提取合法 pair 全集
    """
    all_pairs = set()
    for combo in valid_combos:
        all_pairs.update(extract_pairs_from_combo(combo))
    return all_pairs


def get_covered_pairs(combos: List[Dict[str, str]]) -> set:
    """
    统计一组组合实际覆盖到的 pair
    """
    covered_pairs = set()
    for combo in combos:
        covered_pairs.update(extract_pairs_from_combo(combo))
    return covered_pairs


def calculate_pairwise_coverage(combos: List[Dict[str, str]]) -> float:
    """
    计算 2-pairs 覆盖率
    """
    valid_combos = generate_all_valid_combos()
    all_valid_pairs = get_all_valid_pairs(valid_combos)
    covered_pairs = get_covered_pairs(combos)

    if not all_valid_pairs:
        return 0.0

    return len(covered_pairs) / len(all_valid_pairs)


if __name__ == "__main__":
    random_combos = generate_random_unique_combos(n=14, seed=42)
    coverage = calculate_pairwise_coverage(random_combos)
    print(f"Random combinations pairwise coverage: {coverage:.2%}")