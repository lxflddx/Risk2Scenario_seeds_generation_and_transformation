import os
import json
"""
把从各个事故报告中提取出来的风险因素分层整理一下
"""

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_and_combine_json_files(folder_path):
    combined_data = {
        "risk_factor_classification": {"Road Layer": [], "Infrastructure Layer": [], "Object Interaction Layer": [],
                                       "Weather Layer": []}}

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):  # 确保是JSON文件
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

                # 合并Road Layer
                combined_data["risk_factor_classification"]["Road Layer"].extend(
                    data["risk_factor_classification"]["Road Layer"])

                # 合并Infrastructure Layer
                combined_data["risk_factor_classification"]["Infrastructure Layer"].extend(
                    data["risk_factor_classification"]["Infrastructure Layer"])

                # 合并Object Interaction Layer
                combined_data["risk_factor_classification"]["Object Interaction Layer"].extend(
                    data["risk_factor_classification"]["Object Interaction Layer"])

                # Weather Layer通常为空，如果有内容，也可以类似处理
                combined_data["risk_factor_classification"] ["Weather Layer"].extend(
                    data["risk_factor_classification"] ["Weather Layer"])

    return combined_data


# def show_result(file_path):
#     result = read_file(file_path).replace("\\n", "\n")
#     print(result)
#
#
# show_result('D:\\pythonProject\\LLM_Scenario\\ex_result.txt')

# 设置文件夹路径
folder_path = r'D:\pythonProject\LLM_Scenario\new_risk_json\new_risk_json_intersection'

# 读取并合并JSON文件
combined_json_data = read_and_combine_json_files(folder_path)

# 将合并后的数据写入新的JSON文件
with open('../new_risk_json/new_risk_json_intersection/all_risk_json_intersection.json', 'w', encoding='utf-8') as output_file:
    json.dump(combined_json_data, output_file, indent=2)

