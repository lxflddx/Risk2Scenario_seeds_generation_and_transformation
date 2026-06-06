import re
import json
import os
"""把提取出的风险部分的json数据保存到文件"""


def extract_json_from_text_without_tags(text):
    """
    从文本中提取 JSON 部分并去除标记
    :param text: 含有 JSON 的文本
    :return: 提取出的 JSON 对象（如果有）
    """
    match = re.search(r'\[JSON\](.*?)\[/JSON\]', text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        json_str = escape_for_json(json_str)  # 提取 JSON 部分并去除首尾空格
        # print(f"找到 JSON 部分: {json_str}")
        return json.loads(json_str)  # 转换为 JSON 对象
    else:
        print("未找到 JSON 部分")
        return None


def escape_for_json(python_str):
    json_str = python_str.encode().decode('unicode_escape')
    return json_str


def save_json_to_file(json_obj, file_path):
    """
    保存 JSON 对象到文件
    :param json_obj: JSON 数据
    :param file_path: 文件路径
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_obj, f, indent=2, ensure_ascii=False)
        print(f"JSON 数据成功保存到 {file_path}")
    except Exception as e:
        print(f"保存 JSON 数据失败: {e}")


def process_text_input(input_file_path, output_folder_path):
    """
    综合处理输入文本：提取 JSON，去掉转义符并保存到文件
    :param input_file_path: 输入文件路径
    :param output_folder_path: 输出文件夹路径
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            input_text = f.read()
        extracted_json = extract_json_from_text_without_tags(input_text)
        if extracted_json:
            output_file_path = os.path.join(output_folder_path,
                                            os.path.basename(input_file_path).replace('.txt', '.json'))
            save_json_to_file(extracted_json, output_file_path)
        else:
            print(f"跳过文件（JSON 解析失败）: {os.path.basename(input_file_path)}")
    except Exception as e:
        print(f"处理输入文本失败：{e}")


def process_folder(input_folder_path, output_folder_path):
    """
    处理文件夹中的文本：提取 JSON，去掉转义符并保存到文件
    :param input_folder_path:
    :param output_folder_path:
    :return:
    """
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
    for file_name in os.listdir(input_folder_path):
        if file_name.endswith('.txt'):
            input_file_path = os.path.join(input_folder_path, file_name)
            process_text_input(input_file_path, output_folder_path)


# 示例文本
# input_text = read_file("D:\\pythonProject\\LLM_Scenario\\new_risk_reports_output\\2005041508581.txt")
# print(input_text)
#
# # 运行处理流程
# output_file = "output.json"
# process_text_input(input_text, output_file)
#--------------------------单个和批量处理--------------------
# 输入文件夹路径
input_folder_path = r"/structured_risk/without_cot_txt"
# 输出文件夹路径
output_folder_path = r"/structured_risk/without_cot_json"

# 运行处理流程
process_folder(input_folder_path, output_folder_path)
