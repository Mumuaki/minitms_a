
import time
import subprocess
import sys

print("Waiting 15 seconds to release browser lock...")
time.sleep(15)
print("Starting test...")
subprocess.run([sys.executable, "test_scraper_multiple.py"])
