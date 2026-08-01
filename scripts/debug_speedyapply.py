from sources import speedyapply

print("Fetching raw markdown...")
text = speedyapply.fetch_markdown()
print(f"Fetched {len(text)} characters")

lines = text.split("\n")
print(f"Total lines: {len(lines)}")

header_lines = [l for l in lines if l.strip().startswith("|") and "Company" in l and "Position" in l]
print(f"Header rows detected: {len(header_lines)}")
for h in header_lines:
    print("  ", h[:80])

print("\nCalling get_jobs()...")
jobs = speedyapply.get_jobs()
print(f"Jobs found: {len(jobs)}")
if jobs:
    print("First job:", jobs[0])