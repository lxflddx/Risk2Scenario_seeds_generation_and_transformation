import json
import random
import os
import datetime


def parse_input_string(input_str):
    """
    解析输入字符串，转换为字典格式
    """
    items = input_str.split('\t')

    input_mapping = {
        'RoadCurvature': ['Straight', 'Curve'],
        'RoadGrade': ['Flat', 'Downhill', 'Uphill'],
        'RoadsideSafetyZone': ['WideShoulder', 'RigidObstacle'],
        'FollowingBehavior': ['SafeFollowing', 'FollowingTooClosely'],
        'SpeedInteraction': ['SpeedCoordination', 'LargeSpeedDifference'],
        'KeyVehicleBehavior': ['NormalDriving', 'EmergencyBraking', 'IllegalCutIn', 'IllegalEvasion'],
        'RoadFrictionCoefficient': ['Dry', 'Slippery'],
        'VisibilityConditions': ['Good', 'Nighttime', 'AdverseWeather']
    }

    db_factor_mapping = {
        'RoadCurvature': 'Road Curvature',
        'RoadGrade': 'Road Grade',
        'RoadsideSafetyZone': 'Roadside Safety Zone',
        'FollowingBehavior': 'Following Behavior',
        'SpeedInteraction': 'Speed Interaction',
        'KeyVehicleBehavior': 'Key Vehicle Behavior',
        'RoadFrictionCoefficient': 'Road Friction Coefficient',
        'VisibilityConditions': 'Visibility Conditions'
    }

    safe_values = {
        'RoadCurvature': ['Straight'],
        'RoadGrade': ['Flat'],
        'RoadsideSafetyZone': ['WideShoulder'],
        'FollowingBehavior': ['SafeFollowing'],
        'SpeedInteraction': ['SpeedCoordination'],
        'KeyVehicleBehavior': ['NormalDriving'],
        'RoadFrictionCoefficient': ['Dry'],
        'VisibilityConditions': ['Good']
    }

    level_mapping = {
        'RoadCurvature': {'Straight': 'Straight Road', 'Curve': 'Curved Road'},
        'RoadGrade': {'Flat': 'Level Road', 'Downhill': 'Downhill', 'Uphill': 'Uphill'},
        'RoadsideSafetyZone': {'WideShoulder': 'Wide Shoulder', 'RigidObstacle': 'Rigid Obstacle (Guardrail/Wall)'},
        'FollowingBehavior': {'SafeFollowing': 'Safe Following', 'FollowingTooClosely': 'Following Too Closely'},
        'SpeedInteraction': {'SpeedCoordination': 'Speed Coordination', 'LargeSpeedDifference': 'Large Longitudinal Speed Difference'},
        'KeyVehicleBehavior': {'NormalDriving': 'Normal Driving', 'EmergencyBraking': 'Emergency Braking',
                               'IllegalCutIn': 'Illegal Lane Change/Cut-in', 'IllegalEvasion': 'Illegal Evasion'},
        'RoadFrictionCoefficient': {'Dry': 'Dry', 'Slippery': 'Slippery'},
        'VisibilityConditions': {'Good': 'Good', 'Nighttime': 'Nighttime', 'AdverseWeather': 'Adverse Weather (Rain/Fog)'}
    }

    result = {}
    index = 0
    template_order = [
        'RoadCurvature', 'RoadGrade', 'RoadsideSafetyZone',
        'FollowingBehavior', 'SpeedInteraction', 'KeyVehicleBehavior',
        'RoadFrictionCoefficient', 'VisibilityConditions'
    ]

    for factor in template_order:
        values = input_mapping[factor]
        if index < len(items) and items[index] in values:
            input_value = items[index]
            db_level = level_mapping[factor].get(input_value, input_value)
            is_safe = input_value in safe_values.get(factor, [])
        else:
            input_value = values[0]
            db_level = level_mapping[factor].get(values[0], values[0])
            is_safe = True

        # 确定层级
        if factor in ['RoadsideSafetyZone']:
            layer = 'Infrastructure Layer'
        elif factor in ['FollowingBehavior', 'SpeedInteraction', 'KeyVehicleBehavior']:
            layer = 'Object Interaction Layer'
        elif factor in ['RoadFrictionCoefficient', 'VisibilityConditions']:
            layer = 'Environment Layer'
        else:
            layer = 'Road Layer'

        result[factor] = {
            'input_value': input_value,
            'db_factor': db_factor_mapping.get(factor, factor),
            'db_level': db_level,
            'is_safe': is_safe,
            'layer': layer
        }
        index += 1
    return result


def load_risk_descriptions(file_path):
    """加载风险描述JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载失败: {e}")
        return {}


def find_risk_descriptions(input_dict, risk_data, random_seed=42):
    """单次采样查找风险描述"""
    random.seed(random_seed)
    result = []

    for factor, factor_data in input_dict.items():
        if factor_data['is_safe']:
            continue

        db_factor = factor_data['db_factor']
        db_level = factor_data['db_level']
        expected_layer = factor_data['layer']

        matches = []
        for layer, items in risk_data.items():
            if expected_layer and layer != expected_layer:
                continue
            for item in items:
                if isinstance(item, dict) and 'risk_factor' in item and 'accident_report_id' in item:
                    rf = item['risk_factor']
                    if rf.get('Risk Factor') == db_factor and rf.get('Risk Level') == db_level:
                        matches.append({
                            'Layer': layer,
                            'Risk Factor': rf.get('Risk Factor'),
                            'Risk Level': rf.get('Risk Level'),
                            'Specific Description': rf.get('Specific Description', ''),
                            'Accident Report ID': item['accident_report_id']
                        })

        if matches:
            selected = random.choice(matches)
            result.append({
                'Input Factor': factor,
                'Input Value': factor_data['input_value'],
                'Layer': selected['Layer'],
                'Risk Factor': selected['Risk Factor'],
                'Risk Level': selected['Risk Level'],
                'Specific Description': selected['Specific Description'],
                'Accident Report ID': selected['Accident Report ID']
            })
        else:
            result.append({
                'Input Factor': factor,
                'Input Value': factor_data['input_value'],
                'Layer': expected_layer,
                'Risk Factor': db_factor,
                'Risk Level': db_level,
                'Specific Description': f"No description found for {db_factor} with level {db_level}",
                'Accident Report ID': 'N/A'
            })
    return result


def save_results(results, output_path):
    """保存结果到JSON文件"""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        save_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_risk_factors": len(results),
            "detailed_results": results
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        print(f"结果已保存至: {output_path}")
        return True
    except Exception as e:
        print(f"保存失败: {e}")
        return False


def main():
    """
    Straight\tFlat\tWideShoulder\tSafeFollowing\tLargeSpeedDifference\tIllegalCutIn\tSlippery\tAdverseWeather
    Straight\tUphill\tRigidObstacle\tSafeFollowing\tSpeedCoordination\tNormalDriving\tDry\tGood
    Straight\tDownhill\tWideShoulder\tSafeFollowing\tSpeedCoordination\tIllegalCutIn\tSlippery\tGood
    Straight\tDownhill\tRigidObstacle\tFollowingTooClosely\tLargeSpeedDifference\tIllegalEvasion\tDry\tNighttime
    Curve\tFlat\tRigidObstacle\tSafeFollowing\tSpeedCoordination\tEmergencyBraking\tSlippery\tAdverseWeather
    Straight\tDownhill\tWideShoulder\tFollowingTooClosely\tLargeSpeedDifference\tNormalDriving\tSlippery\tAdverseWeather
    Straight\tUphill\tWideShoulder\tFollowingTooClosely\tLargeSpeedDifference\tIllegalCutIn\tSlippery\tNighttime
    Curve\tFlat\tWideShoulder\tSafeFollowing\tSpeedCoordination\tNormalDriving\tDry\tNighttime
    Straight\tUphill\tWideShoulder\tSafeFollowing\tSpeedCoordination\tIllegalEvasion\tSlippery\tAdverseWeather
    Straight\tFlat\tWideShoulder\tFollowingTooClosely\tLargeSpeedDifference\tEmergencyBraking\tDry\tGood
    Straight\tDownhill\tWideShoulder\tFollowingTooClosely\tLargeSpeedDifference\tEmergencyBraking\tSlippery\tNighttime
    Curve\tFlat\tRigidObstacle\tFollowingTooClosely\tLargeSpeedDifference\tIllegalCutIn\tDry\tGood
    Curve\tFlat\tWideShoulder\tFollowingTooClosely\tLargeSpeedDifference\tIllegalEvasion\tSlippery\tGood
    Straight\tUphill\tRigidObstacle\tSafeFollowing\tSpeedCoordination\tEmergencyBraking\tDry\tNighttime
"""
    input_str = "Straight\tUphill\tRigidObstacle\tSafeFollowing\tSpeedCoordination\tEmergencyBraking\tDry\tNighttime"

    parsed = parse_input_string(input_str)
    risk_data = load_risk_descriptions(r"/risk2scenario/search/risk_library_combination.json")

    if not risk_data:
        return None

    results = find_risk_descriptions(parsed, risk_data, random_seed=42)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"D:\\pythonProject\\LLM_Scenario\\search_risk_results\\14combine\\search_risk_results_single_{timestamp}.json"
    save_results(results, output_file)

    print("\n匹配结果：")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['Risk Factor']} - {r['Risk Level']} (ID: {r['Accident Report ID']})")

    return [{
        'Risk Level': r['Risk Level'],
        'Specific Description': r['Specific Description'],
        'Accident Report ID': r['Accident Report ID'],
        'Risk Factor': r['Risk Factor']
    } for r in results]


if __name__ == "__main__":
    main()