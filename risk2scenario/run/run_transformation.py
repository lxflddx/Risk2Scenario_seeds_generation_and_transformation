import json
import time
import os
import argparse
import openpyxl

# 本文方法（TAS → Logic JSON）
from risk2scenario.generate.generate_TAS import ExtractTAS
from risk2scenario.generate.generata_logic_json import TASToLogicalScenario

# LeGEND方法（IPS → Test Case）
from risk2scenario.generate.generate_ips import ExtractIps
from risk2scenario.generate.generate_test_case import IpsToTestcase

# 如果需要 AST 转换（仅用于 IPS 方法）
import ast
import astunparse


def run_tas_method(input_excel, output_dir, max_row=15):
    """
    执行本文方法：事故报告 → TAS → Logical Scenario JSON
    """
    print("=" * 60)
    print("Running TAS method (Ours)")
    print("=" * 60)

    workbook = openpyxl.load_workbook(input_excel)
    sheet = workbook.active
    data_rows = sheet.iter_rows(min_row=2, max_row=max_row, values_only=True)

    extract_tas = ExtractTAS()
    tas_to_logical = TASToLogicalScenario()

    os.makedirs(output_dir, exist_ok=True)

    extract_times = []
    convert_times = []
    start_time = time.time()

    for row in data_rows:
        scenario_id = row[0]
        report = row[1]

        print(f"\nProcessing Scenario {scenario_id}")
        print("Accident Report:", report[:100], "...")

        # Stage 1: Report -> TAS
        extract_start = time.time()
        try:
            tas_result = extract_tas.extract(report)
        except Exception as e:
            print(f"[ERROR] TAS extraction failed: {e}")
            continue
        extract_time = time.time() - extract_start
        extract_times.append(extract_time)
        print(f"TAS Extraction Time: {extract_time:.4f}s")

        # Stage 2: TAS -> Logical Scenario
        convert_start = time.time()
        try:
            logical_result = tas_to_logical.convert(tas_result)
        except Exception as e:
            print(f"[ERROR] Logical conversion failed: {e}")
            continue
        convert_time = time.time() - convert_start
        convert_times.append(convert_time)
        print(f"Logical Conversion Time: {convert_time:.4f}s")

        # Save result
        save_data = {
            "scenario_id": scenario_id,
            "accident_report": report,
            "tas_scenario": tas_result,
            "logical_scenario": logical_result
        }
        save_path = os.path.join(output_dir, f"{scenario_id}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)
        print(f"Saved to: {save_path}")

    # Statistics
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("Finished TAS method")
    if extract_times:
        print(f"Average TAS Extraction Time: {sum(extract_times)/len(extract_times):.4f}s")
    if convert_times:
        print(f"Average Logical Conversion Time: {sum(convert_times)/len(convert_times):.4f}s")
    print(f"Total Runtime: {total_time:.4f}s")


def run_ips_method(input_excel, output_dir, max_row=15):
    """
    执行 LeGEND 方法：事故报告 → IPS → Test Case (AST 代码)
    """
    print("=" * 60)
    print("Running IPS method (LeGEND)")
    print("=" * 60)

    workbook = openpyxl.load_workbook(input_excel)
    sheet = workbook.active
    data_rows = sheet.iter_rows(min_row=2, max_row=max_row, values_only=True)

    extract_ips = ExtractIps()
    ips_to_testcase = IpsToTestcase()

    os.makedirs(output_dir, exist_ok=True)

    extract_times = []
    convert_times = []
    start_time = time.time()

    for row in data_rows:
        scenario_id = row[0]
        report = row[1]

        print(f"\nProcessing Scenario {scenario_id}")
        print("Accident Report:", report[:100], "...")

        # Stage 1: Report -> IPS
        extract_start = time.time()
        try:
            ips_result = extract_ips.extract(report)
        except Exception as e:
            print(f"[ERROR] IPS extraction failed: {e}")
            continue
        extract_time = time.time() - extract_start
        extract_times.append(extract_time)
        print(f"IPS Extraction Time: {extract_time:.4f}s")

        # Stage 2: IPS -> Test Case (AST)
        convert_start = time.time()
        try:
            testcase_ast = ips_to_testcase.convert(ips_result)
        except Exception as e:
            print(f"[ERROR] Test case conversion failed: {e}")
            continue
        convert_time = time.time() - convert_start
        convert_times.append(convert_time)
        print(f"Test case conversion Time: {convert_time:.4f}s")

        # Convert AST to source code string
        testcase_code = astunparse.unparse(ast.fix_missing_locations(testcase_ast.update_ast_node()))
        testcase_code = testcase_code.replace("\\n", "\n")

        # Save result
        save_data = {
            "scenario_id": scenario_id,
            "accident_report": report,
            "functional_scenario": ips_result,
            "logical_scenario": testcase_code
        }
        save_path = os.path.join(output_dir, f"{scenario_id}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4, ensure_ascii=False)
        print(f"Saved to: {save_path}")

    # Statistics
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("Finished IPS method")
    if extract_times:
        print(f"Average IPS Extraction Time: {sum(extract_times)/len(extract_times):.4f}s")
    if convert_times:
        print(f"Average Test Case Conversion Time: {sum(convert_times)/len(convert_times):.4f}s")
    print(f"Total Runtime: {total_time:.4f}s")


def main():
    parser = argparse.ArgumentParser(description="Unified two-stage transformation for risk2scenario")
    parser.add_argument("--input", "-i", required=True, help="Path to input Excel file (accident reports)")
    parser.add_argument("--method", "-m", required=True, choices=["tas", "ips"],
                        help="Transformation method: 'tas' (ours) or 'ips' (LeGEND)")
    parser.add_argument("--output_dir", "-o", default=None,
                        help="Output directory for JSON results. If not given, auto-generate based on method and input name.")
    parser.add_argument("--max_row", type=int, default=15,
                        help="Maximum row to process (default: 15)")
    args = parser.parse_args()

    # Determine output directory
    if args.output_dir is None:
        base_name = os.path.splitext(os.path.basename(args.input))[0]
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "result_time_test",
            args.method.upper()
        )
    else:
        output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    if args.method == "tas":
        run_tas_method(args.input, output_dir, max_row=args.max_row)
    else:  # ips
        run_ips_method(args.input, output_dir, max_row=args.max_row)


if __name__ == "__main__":
    main()