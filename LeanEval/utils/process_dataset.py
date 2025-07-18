import os
import re
import json
from pathlib import Path
import sys
import argparse

# 确保 LeanEval 可以被导入 (调整路径)
LEAN_EVAL_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(LEAN_EVAL_ROOT))

try:
    from LeanEval.datasets import downloader
    from LeanEval.datasets.schema import LeanItem
except ImportError:
    print("错误: 无法导入 LeanEval 模块。请确保脚本在正确的项目结构中运行。")
    sys.exit(1)

# 用于查找定理/引理及其陈述的正则表达式（简化版）
THEOREM_RE = re.compile(
    r"^(?:theorem|lemma)\s+([\w\.]+)\s*(?:\{.*?\})?\s*(?:\(.*?\))?\s*:\s*(.*?)\s*:=",
    re.MULTILINE | re.DOTALL,
)
# 用于查找 imports 的正则表达式
IMPORT_RE = re.compile(r"^import\s+([\w\.]+)", re.MULTILINE)

def parse_lean_file(file_path: Path) -> list[dict]:
    """解析 Lean 文件以提取定理/引理和 imports。"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"无法读取 {file_path}: {e}")
        return []

    imports = IMPORT_RE.findall(content)
    theorems = []

    for match in THEOREM_RE.finditer(content):
        full_match_text = match.group(0)
        # 尝试查找 'by' 或 'sorry' 来限制陈述部分
        end_match = re.search(r"\s*:=(?:\s*(?:by|sorry|begin))", full_match_text, re.MULTILINE | re.DOTALL)

        if end_match:
            statement_text = full_match_text[:end_match.start()].strip()
            # 清理陈述（移除 theorem/lemma 关键字）
            statement_text = re.sub(r"^(?:theorem|lemma)\s+", "", statement_text, 1)
            theorems.append({
                "id": f"{file_path.stem}_{match.group(1)}",
                "imports": imports,
                "statement": statement_text.strip(),
                "difficulty": 1, # 默认难度
            })
        else:
             theorems.append({
                 "id": f"{file_path.stem}_{match.group(1)}",
                 "imports": imports,
                 "statement": match.group(0).replace(":=", "").strip(),
                 "difficulty": 1,
            })

    return theorems

def process_dataset(download_path: str, output_json_path: str):
    """将下载的 Lean 文件处理成 JSON 数据集。"""
    lean_files = list(Path(download_path).rglob("*.lean"))
    all_items = []

    print(f"找到 {len(lean_files)} 个 .lean 文件进行处理...")

    for lean_file in lean_files:
        items = parse_lean_file(lean_file)
        all_items.extend(items)

    print(f"提取到 {len(all_items)} 个潜在的定理/引理。")

    lean_items_data = []
    for item_data in all_items:
        try:
            if item_data.get("statement"):
                LeanItem(**item_data) # 使用 Pydantic 进行验证
                lean_items_data.append(item_data)
        except Exception as e:
            print(f"因验证错误跳过项目 {item_data.get('id')}: {e}")

    print(f"正在保存 {len(lean_items_data)} 个有效项目到 {output_json_path}...")
    Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(lean_items_data, f, indent=2, ensure_ascii=False)
    print("处理完成。")

def main():
    """主函数，用于下载和处理数据集。"""
    parser = argparse.ArgumentParser(description="下载并处理 Lean 数据集为 JSON 格式。")
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="leanprover-community/miniF2F",
        help="要下载的 Hugging Face 数据集 ID (例如 'leanprover-community/miniF2F')。"
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        default=str(LEAN_EVAL_ROOT / "data" / "downloaded"),
        help="数据集下载目录。"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=str(LEAN_EVAL_ROOT / "data" / "json" / "minif2f_processed.json"),
        help="处理后的 JSON 输出文件路径。"
    )
    args = parser.parse_args()

    download_dir = Path(args.download_dir)
    output_json = Path(args.output_json)
    dataset_id = args.dataset_id
    dataset_name = dataset_id.split('/')[-1]
    local_dataset_path = download_dir / dataset_name

    download_dir.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    print(f"--- 开始处理 {dataset_id} ---")
    print(f"目标 Hugging Face ID: {dataset_id}")
    print(f"下载位置: {local_dataset_path}")
    print(f"输出 JSON: {output_json}")

    # 使用 downloader 下载
    downloader._download_huggingface_dataset(dataset_id, str(download_dir))

    # 处理
    if local_dataset_path.exists():
        process_dataset(str(local_dataset_path), str(output_json))
    else:
        print(f"错误: 下载路径 {local_dataset_path} 不存在。")

if __name__ == "__main__":
    main()