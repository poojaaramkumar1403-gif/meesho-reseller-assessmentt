# Run unittest to verify part2 tests pass
import subprocess

res = subprocess.run(["python3", "-m", "unittest", f"{repo_dir}/part2_engine/test_growth_engine.py"], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)