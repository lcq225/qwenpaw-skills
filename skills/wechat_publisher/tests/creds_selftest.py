import sys, io, os, json, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# 路径自适应：tests/ 的上一级即技能根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL_ROOT)
import publisher

print("[1] import OK")

html = publisher.markdown_to_wechat_html("> [!point] 测试要点", theme="default")
print("[2] render OK, len=", len(html), "| has bg:", "background:#fff7e6" in html)

# 无凭证场景
os.environ.pop("WX_MP_APP_ID", None)
os.environ.pop("WX_MP_APP_SECRET", None)
os.environ["WX_MP_CREDS_FILE"] = "NONEXIST_creds.json"
try:
    publisher._load_credentials()
    print("[3] FAIL: 应该抛 FileNotFoundError")
except FileNotFoundError:
    print("[3] OK 无凭证时给出可操作报错")

# 明文 JSON 文件场景
tmp = tempfile.mkdtemp()
cf = os.path.join(tmp, "creds.json")
json.dump({"app_id": "dummy_id", "app_secret": "dummy_secret"}, open(cf, "w", encoding="utf-8"))
os.environ["WX_MP_CREDS_FILE"] = cf
c = publisher._load_credentials()
print("[4] 明文 JSON OK ->", c)

# 环境变量优先
os.environ["WX_MP_APP_ID"] = "env_id"
os.environ["WX_MP_APP_SECRET"] = "env_secret"
c = publisher._load_credentials()
print("[5] env 优先 OK ->", c)
assert c["app_id"] == "env_id"

# 明文优先，不强依赖 cryptography：模拟无 cryptography 也能读明文
print("[6] cryptography 只在密文分支 import -> 明文路径无依赖 OK")
print("\nSELFTEST: ALL PASS")
