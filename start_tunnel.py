import subprocess
import time
import re

print("Starting public tunnel via localhost.run on 127.0.0.1:8000...")
p = subprocess.Popen(
    "ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:127.0.0.1:8000 nokey@localhost.run",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

for line in p.stdout:
    line_clean = line.strip()
    if "tunneled with tls termination" in line_clean:
        m = re.search(r"https://[a-zA-Z0-9.-]+", line_clean)
        if m:
            print("==================================================")
            print("LIVE PUBLIC DEMO URL:", m.group(0))
            print("==================================================")
            with open("live_demo_link.txt", "w") as f:
                f.write(m.group(0))
            break

p.wait()
