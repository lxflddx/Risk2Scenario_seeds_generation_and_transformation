# risk2scenario_seeds_generation_and_transformation
本项目实现了基于风险知识增强的种子场景生成与转换：  
1. 从原始事故数据中**提取风险**（支持 CoT / 非 CoT 两种方式）  
2. 构建**JOSN结构化风险知识库**  
3. 提供两种增强种子场景生成方法，对应两种风险检索方法：**语义相似度搜索** 与 **基于标签组合的随机采样**  
4. 基于检索到的风险**生成增强场景描述**  
5. 通过**两阶段转换**（功能场景 → 中间表示 → 逻辑场景）输出可用于仿真器的测试脚本

## 核心功能说明

### 1. 风险提取 (`extract/`)
从原始文本或日志中提取自动驾驶风险事件。支持两种模式：
- **`llm_risk_extract.py`**：使用大语言模型并按 **思维链（CoT）** 方式推理，准确性更高。
- **`without_cot_extract.py`**：不使用 CoT，用于对比实验。

提取结果会以结构化形式保存在 `structured_risk/` 下。

### 2. 构建结构化风险知识库 
- `structured_risk/with_cot_all20.json` 等文件是从20条事故报告中提取出的包含71条风险的风险知识库。  

### 3. 相关风险检索 (`search/`)
提供两种风险的检索采样方式：

| 方法 | 使用库 | 脚本 | 说明 |
|------|--------|------|------|
| **语义相似度搜索** | `risk_library_semantic.json` | `search_query_risks.py` | 输入基础场景描述，返回向量空间中最相似的 top-3 风险。 |
| **2-way组合随机采样** | `risk_library_combination.json` | `search_combine_risks.py` | 根据风险标签的 2-way 组合，随机采样匹配的风险描述。 |
| **随机组合（对比）** | `risk_library_combination.json` | `random_risk_combine.py` | 完全随机采样，用于消融实验。 |

### 4. 生成增强种子场景描述 (`generate/`, `g_prompt/`, `data/`)
- 输入：`search_results/` 中存放的检索到的具体风险因素描述 + 基础场景描述 / 风险组合标签。  
- **处理**：
  - 运行 `generate_discription.py`，结合 `g_prompt/` 下的模板：
    - `generate_description_CT.txt`：用于组合测试增强场景生成。
    - `generate_description_SR.txt`：用于语义检索增强场景生成。
  - 运行 text_to_excel.py，将生成的场景描述或原始事故报告解析并写入结构化表格。
- **输出**：结构化的场景描述表格（`.xlsx`），存放于 `data/` 目录，供下游转换使用。

### 5. 两阶段转换生成测试用例 (`run/`)
将 `data/` 中的增强场景描述（Excel 文件）通过两阶段转换，转化为逻辑场景测试用例。提供两种方法，通过 `--method` 参数切换：

| 方法 | 参数值 | 说明 |
|------|--------|------|
| 本文方法 | `tas` | 事故报告 → TAS（时空动作序列） → 逻辑场景 JSON |
| LeGEND方法 | `ips` | 事故报告 → IPS（交互模式序列） → 文本测试用例 |

**统一运行命令**：
```bash
# 本文方法（TAS → Logic JSON）
python run/run_transformation.py --input data/risk2Scenario_CT.xlsx --method tas

# LeGEND方法（IPS → Test Case）
python run/run_transformation.py --input data/risk2scenario_2.xlsx --method ips
```

**参数说明**：
- `--input` / `-i`：必选，Excel 文件路径（第一列为场景ID，第二列为事故报告描述）。
- `--method` / `-m`：必选，可选 `tas` 或 `ips`。
- `--output_dir` / `-o`：可选，指定输出目录（默认 `data/result_time_test/方法名/`）。
- `--max_row`：可选，处理的最大行数（默认 15）。

输出结果：每个场景保存为一个 JSON 文件，包含原始报告、中间表示和最终测试用例/逻辑场景。

---

## 三个风险知识库说明

本项目维护**三个不同用途的风险库**，均存放于 `search/` 目录：

| 文件名 | 用途 | 来源说明 |
|--------|------|----------|
| `risk_library_structured.json` | **论文第三章核心风险库** | 从20条事故报告中按预定义的分层风险体系提取，共包含71条结构化风险条目。 |
| `risk_library_semantic.json` | **语义检索专用库** | 早期从高速公路事故数据中提取，未严格遵循分层结构，适合自由文本相似度匹配。 |
| `risk_library_combination.json` | **组合测试采样专用库** | 同样按预定义分层风险提取（方法与结构化库一致），但因提取模型/参数差异，条目内容与结构化库不完全相同。 |

三个库独立使用，分别对应不同的检索策略。`calculate_pairs.py` 会为每个库生成独立的嵌入向量文件和 FAISS 索引（文件名自动区分）。

## 项目目录树
```
LLM_Scenario/
├── g_prompt/                         # 提示词模板
├── risk2scenario/                    # 核心转换模块
│   ├── extract/                      # 风险提取
│   │   ├── llm_risk_extract.py       # CoT风险提取
│   │   └── without_cot_extract.py    # 无CoT风险提取，对比实验
│   ├── generate/                     # 场景生成与转换
│   │   ├── generate_discription.py   # 生成增强种子场景描述
│   │   ├── generate_TAS.py           # 第一阶段（本文方法）：TAS
│   │   ├── generate_logic_json.py    # 第二阶段（本文方法）：TAS → Logic JSON
│   │   ├── generate_ips.py           # 第一阶段（LeGEND方法）：IPS
│   │   ├── generate_test_case.py     # 第二阶段（LeGEND方法）：IPS → Test Case
│   │   └── scenario_model.py 
│   └── run/                          # 运行
│       └── run_transformation.py     
├── search/                           # 风险知识库检索
│   ├── risk_library_semantic.json    # 语义检索库（早期提取）
│   ├── risk_library_combination.json # 组合测试采样库（按预定义提取）
│   ├── calculate_pairs.py            # 计算风险标签组合的两两覆盖
│   ├── search_query_risks.py         # 语义相似度检索
│   ├── search_combine_risks.py       # 2-way组合标签采样
│   └── random_risk_combine.py        # 随机采样（对比实验）
├── search_results/                   # 检索结果输出目录
│   ├── CT_search_results/            # 组合测试检索采样结果
│   └── SR_search_results/            # 语义检索结果
├── structured_risk/                  # 提取的风险
│   ├── with_cot_json/                
│   ├── with_cot_txt/                 
│   ├── without_cot_json/
│   └── without_cot_txt/
├── utils/                            # 工具
│   ├── file_util.py                  # 分层整理风险
│   ├── llm_util.py                   # 大模型配置
│   ├── openai_llm_utils.py           # openai大模型配置
│   ├── process_json_util.py          # 把提取出的风险部分的json数据保存到文件中
│   ├── process_testcase.py           # 将转换得到的json测试用例提取到表格中，便于后续运行仿真
│   └── text_to_excel.py              # 处理事故报告或事故描述，将其存储到表格中，便于后续转换
├── data/                             # 生成的增强场景描述（.xlsx）以及它们的转换结果
│   ├── combine_gemma_12b/
│   ├── risk2Scenario_C2/
│   ├── risk2Scenario_CT/
│   ├── risk2Scenario_S2/
│   └── risk2Scenario_SR/
├── README.md
└── requirements.txt
```

