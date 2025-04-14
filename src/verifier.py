import subprocess #用于执行命令行
from typing import Tuple 

def verify_lean_file(filename) -> Tuple[bool, str]:  # ✅ TODO: 改为参数传入文件名
    """
    调用 lean 命令运行 .lean 文件

    Args:
        values (str): 文件路径

    Returns:
        Tuple[bool, str]: 运行结果

    Raises:
        None
    """
    try:
        result = subprocess.run(
            ["lake", "env", "lean", filename],          # 使用 --run 执行 Lean 脚本
            capture_output=True,                        # 捕获标准输出和标准错误
            text=True,                                  # 将输出解码为字符串
            cwd="../",                                  # 设置工作目录为项目根目录
            timeout=100,                                # 设置超时时间
        )
    except subprocess.TimeoutExpired:
        return False, "Lean 超时"

    return result.returncode, result.stdout

if __name__ == "__main__":

    # ✅ TODO: 添加正例和反例
    # 正例：一个可以成功运行的 Lean 文件
    good_file = "examples/simple_proof.lean"

    # 反例：一个会报错的 Lean 文件（比如语法错误）
    bad_file = "examples/simple_proof_wrong.lean"

    print("🟢 正例测试:")
    good_output = verify_lean_file(good_file)
    if good_output:
        print("✅ Lean 执行成功，返回信息如下：")
        print("Return code:", good_output[0])
        print("stdout:\n", good_output[1])

    print("\n🔴 反例测试:")
    bad_output = verify_lean_file(bad_file)
    if bad_output:
        print("❌ Lean 执行失败，返回信息如下：")
        print("Return code:", bad_output[0])
        print("stdout:\n", bad_output[1])

