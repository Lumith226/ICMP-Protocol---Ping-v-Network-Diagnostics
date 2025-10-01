import subprocess
import re

HOSTS = ["google.com", "cloudflare.com", "facebook.com"]
PING_COUNT = 4
RUN_TRACERT_FOR = "facebook.com"

def run_cmd(cmd_list):
    result = subprocess.run(cmd_list, capture_output=True, text=True, errors="ignore")
    return result.stdout

def parse_loss_percent(text):
    m = re.search(r"(\d+)%.*loss", text, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None

def parse_avg_ms(text):
    m = re.search(r"Average\s*=\s*(\d+)\s*ms", text, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None

def ping_windows(host, count):
    out = run_cmd(["ping", "-n", str(count), host])
    avg_ms = parse_avg_ms(out)
    loss_percent = parse_loss_percent(out)
    return {"host": host, "avg_ms": avg_ms, "loss_percent": loss_percent, "raw": out}

def tracert_windows(host, max_hops=30, no_dns=True):
    cmd = ["tracert"]
    if no_dns:
        cmd.append("-d")
    cmd += ["-h", str(max_hops), host]
    out = run_cmd(cmd)
    print("\n=== THEO DÕI ĐƯỜNG DẪN (TRACERT) ===")
    print(out)

def main():
    summaries = []
    print("=== CHẠY PING ===")
    for h in HOSTS:
        res = ping_windows(h, PING_COUNT)
        print(f"\n--- {h} ---")
        print(res["raw"])
        summaries.append(res)

    print("\n=== TÓM TẮT PING ===")
    print(f"{'Host':<18} {'Avg(ms)':>8} {'Loss(%)':>8}")
    print("-" * 36)
    for r in summaries:
        avg = r['avg_ms'] if r['avg_ms'] is not None else "-"
        loss = r['loss_percent'] if r['loss_percent'] is not None else "-"
        print(f"{r['host']:<18} {str(avg):>8} {str(loss):>8}")

    tracert_windows(RUN_TRACERT_FOR)

if __name__ == "__main__":
    main()
