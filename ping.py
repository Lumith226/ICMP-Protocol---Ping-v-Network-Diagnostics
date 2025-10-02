import subprocess, re, json, sys
from concurrent.futures import ThreadPoolExecutor

HOSTS = ["google.com", "cloudflare.com", "facebook.com"]
PING_COUNT = 4
RTT_THRESHOLD = 100  # ms
LOSS_THRESHOLD = 10  # %

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
    return out

def main():
    results = []
    print("=== CHẠY PING SONG SONG ===")
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(ping_windows, h, PING_COUNT) for h in HOSTS]
        for f in futures:
            res = f.result()
            results.append(res)
            print(f"\n--- {res['host']} ---")
            print(res["raw"])

    print("\n=== TÓM TẮT PING ===")
    print(f"{'Host':<18} {'Avg(ms)':>8} {'Loss(%)':>8} {'Status':>10}")
    print("-" * 50)
    problems = []
    for r in results:
        avg = r['avg_ms'] if r['avg_ms'] is not None else "-"
        loss = r['loss_percent'] if r['loss_percent'] is not None else "-"
        status = "OK"
        if isinstance(avg, int) and avg > RTT_THRESHOLD:
            status = "RTT HIGH"
        if isinstance(loss, int) and loss > LOSS_THRESHOLD:
            status = "LOSS HIGH"
        print(f"{r['host']:<18} {str(avg):>8} {str(loss):>8} {status:>10}")
        if status != "OK":
            problems.append(r['host'])

    # Diagnostics log
    with open("net_diag.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Auto traceroute nếu có vấn đề
    if problems:
        print("\n=== THEO DÕI ĐƯỜNG DẪN (TRACERT) ===")
        for h in problems:
            print(f"\nTraceroute to {h}:")
            print(tracert_windows(h))

    # Exit code cho CI/monitoring
    if problems:
        sys.exit(1)

if __name__ == "__main__":
    main()
