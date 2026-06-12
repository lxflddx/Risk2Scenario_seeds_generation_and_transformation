import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import os
import time
import torch

# 设置 PyTorch 显存管理策略，避免碎片化
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# 设置代理
os.environ["http_proxy"] = "http://127.0.0.1:7897"
os.environ["https_proxy"] = "http://127.0.0.1:7897"

# 初始化模型和索引
model = None
index = None
all_risk_data = []


def load_risk_data_and_model(json_path):
    global model, index, all_risk_data
    start_time = time.time()

    # 1. 加载 Sentence-T5 模型（使用 GPU）
    model = SentenceTransformer('sentence-transformers/sentence-t5-large', device='cuda')
    
    # 2. 从 JSON 文件中提取风险数据
    if not os.path.exists(json_path):
        print(f"文件 {json_path} 不存在。")
        exit()

    # 读取 JSON 文件
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 调试输出：查看实际结构
    print(f"JSON 数据类型：{type(data)}")
    if isinstance(data, dict):
        print(f"字典的键：{list(data.keys())}")
    elif isinstance(data, list):
        print(f"列表长度：{len(data)}")

    # 提取所有风险数据
    all_risk_data = []

    # 情况 2：是分层的字典（新格式，如 risk_library_semantic.json）
    if isinstance(data, dict):
        for layer_name, risks in data.items():
            print(f"处理层级：{layer_name}，包含 {len(risks)} 条数据")
            if isinstance(risks, list):
                for risk in risks:
                    if isinstance(risk, dict):
                        all_risk_data.append({
                            "Risk Factor": risk.get('Risk Factor', ''),
                            "Specific Description": risk.get('Specific Description', ''),
                            "Layer": layer_name  # 可选：记录来自哪一层
                        })
    
    # 检查是否提取到数据
    if len(all_risk_data) == 0:
        print(f"错误：未能从 {json_path} 中提取到任何风险数据！")
        exit()
    
    print(f"成功加载 {len(all_risk_data)} 条风险数据")

    # 3. 将风险描述转化为嵌入向量（小批量处理）
    risk_descriptions = [risk['Specific Description'] for risk in all_risk_data]
    embeddings = model.encode(risk_descriptions, batch_size=8, show_progress_bar=True, convert_to_numpy=True)
    
    # 检查嵌入向量是否生成成功
    if len(embeddings) == 0:
        print("错误：模型编码后返回空数组！")
        exit()
    
    print(f"嵌入向量形状：{embeddings.shape}")

    # 4. 创建 faiss 索引
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    embeddings_array = np.array(embeddings, dtype=np.float32)
    index.add(embeddings_array)

    end_time = time.time()
    print(f"数据加载和索引构建完成，耗时：{end_time - start_time} 秒")


def search_risk(query_risk, top_k=3):
    """
    搜索相似风险描述，并去重
    :param query_risk: 查询的风险描述
    :param top_k: 返回的结果数量
    """
    global model, index, all_risk_data
    if model is None or index is None:
        raise ValueError("请先调用 load_risk_data_and_model 函数加载数据和模型！")

    start_time = time.time()

    # 查询最相似的风险描述（多查询一些用于去重）
    query_embedding = model.encode([query_risk], convert_to_numpy=True)[0]
    query_embedding = np.array([query_embedding], dtype=np.float32)
    
    # 查询前 6 个结果
    search_top_k = 6
    distances, indices = index.search(query_embedding, search_top_k)

    print(f"查询风险描述：{query_risk}")
    print(f"\n=== 检索到的所有 {search_top_k} 个结果 ===")
    print("=" * 80)
    
    # 显示所有检索结果
    for i in range(search_top_k):
        if indices[0][i] != -1:
            risk_data = all_risk_data[indices[0][i]]
            print(f"[{i+1}] 距离={distances[0][i]:.6f}, 索引={indices[0][i]}")
            print(f"    Risk Factor: {risk_data['Risk Factor']}")
            print(f"    Specific Description: {risk_data['Specific Description']}")
            if 'Layer' in risk_data:
                print(f"    Layer: {risk_data.get('Layer', 'N/A')}")
            print()
    print("=" * 80)
    
    # 收集所有有效结果的索引和距离
    valid_results = []
    for i in range(search_top_k):
        if indices[0][i] != -1:
            valid_results.append({
                'position': i,
                'index': indices[0][i],
                'distance': distances[0][i],
                'risk_data': all_risk_data[indices[0][i]]
            })
    
    similarity_threshold = 0.001  # 相似度阈值
    
    print(f"\n=== 两两比较去重处理 ===")
    print(f"共 {len(valid_results)} 条有效结果，开始两两比较...\n")
    
    # 标记哪些结果应该被保留
    keep_flags = [True] * len(valid_results)
    
    # 两两比较所有结果
    for i in range(len(valid_results)):
        if not keep_flags[i]:
            continue
            
        for j in range(i + 1, len(valid_results)):
            if not keep_flags[j]:
                continue
            
            # 计算两个结果的距离差
            distance_diff = abs(valid_results[i]['distance'] - valid_results[j]['distance'])
            
            print(f"比较位置 {i+1} 和 {j+1}:")
            print(f"  距离分别为 {valid_results[i]['distance']:.6f} 和 {valid_results[j]['distance']:.6f}")
            print(f"  距离差 = {distance_diff:.6f}", end="")
            
            if distance_diff < similarity_threshold:
                # 高度相似，保留距离更小的那个
                if valid_results[i]['distance'] <= valid_results[j]['distance']:
                    print(f" → 高度相似，保留位置 {i+1}（距离更小），移除位置 {j+1}")
                    keep_flags[j] = False
                else:
                    print(f" → 高度相似，保留位置 {j+1}（距离更小），移除位置 {i+1}")
                    keep_flags[i] = False
                    break  # 位置 i 已被移除，不需要继续比较
            else:
                print(f" → 不相似，都保留")
    
    # 收集最终保留的结果
    final_results = []
    for i in range(len(valid_results)):
        if keep_flags[i]:
            final_results.append(valid_results[i])
    
    # 如果结果超过 top_k 个，只取前 top_k 个
    if len(final_results) > top_k:
        print(f"\n去重后得到 {len(final_results)} 条结果，超过要求的 {top_k} 条，截取前 {top_k} 条")
        final_results = final_results[:top_k]
    
    # 转换为 numpy 数组格式
    final_indices_array = np.array([r['index'] for r in final_results], dtype=np.int32)
    final_distances_array = np.array([r['distance'] for r in final_results], dtype=np.float32)
    
    print(f"\n=== 最终保留的 {len(final_results)} 条结果 ===")
    print(f"最终索引：{final_indices_array}")
    print(f"最终距离：{final_distances_array}")
    
    # 计算平均距离
    if len(final_distances_array) > 0:
        avg_distance = np.mean(final_distances_array)
        print(f"\n平均距离：{avg_distance:.6f}")

    current_risk_file = "/risk2scenario/search\\search_cunfang.txt"

    with open(current_risk_file, 'w', encoding='utf-8') as f_current:
        for i in range(len(final_results)):
            risk_data = final_results[i]['risk_data']
            f_current.write(f"Risk Factor: {risk_data['Risk Factor']}\n")
            f_current.write(f"Specific Description: {risk_data['Specific Description']}\n\n")
            print(f"\n【结果 {i+1}】")
            print(f"Distance: {final_results[i]['distance']:.6f}")
            print(f"Risk Factor: {risk_data['Risk Factor']}")
            print(f"Specific Description: {risk_data['Specific Description']}")

    end_time = time.time()
    print(f"\n查询完成，耗时：{end_time - start_time} 秒")
    print(f"当前运行的结果已写入：{current_risk_file}")



if __name__ == "__main__":
    # folder_path = 'D:\\pythonProject\\LLM_Scenario\\new_risk_json\\new_risk_json_highway_gemma'
    file_path = r'/risk2scenario/search/risk_library_semantic.json'
    load_risk_data_and_model(file_path)
    query_risk = "The ego is driving straight through an intersection when a crossing vehicle runs the red light and unexpectedly accelerates, forcing the ego to quickly reassess the situation and perform a collision avoidance maneuver."
    search_risk(query_risk)
# 检索语句
"""
1.A vehicle stopped to make a left turn was rear-ended by another vehicle traveling in the same direction.
2.A car overtaking another vehicle drifted into the adjacent lane and sideswiped a third vehicle.
3.A vehicle lost control while avoiding a lane-changing car, collided with another vehicle, and then hit the barrier wall.
4.A car drifted out of its lane during a lane change, sideswiping a truck in the adjacent lane.
5.Traffic congestion obscured the view of both drivers, leading to a collision between a vehicle traveling eastbound in lane one and another turning left from the center turn lane.
"""
# 对照检索语句
"""
1_1.A vehicle was rear-ended while slowing down to turn left.
3_1.The ego vehicle is performing a lane change to evade a slow-moving vehicle; the adversarial car in the target lane on the right front suddenly brakes, causing the ego vehicle to react quickly to avoid a collision.
4_1.The ego is driving straight through an intersection when a crossing vehicle runs the red light and unexpectedly accelerates, forcing the ego to quickly reassess the situation and perform a collision avoidance maneuver.

"""