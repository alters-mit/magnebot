from pathlib import Path


txt = Path("../data/turn_constants.csv").read_text()
lines = txt.split("\n")[1:]
min_time = 100000
min_line = ""
for line in lines:
    q = line.split(",")[0]
    if q == "":
        continue
    t = float(q)
    if t < min_time:
        min_time = t
        min_line = line
print(min_line)
