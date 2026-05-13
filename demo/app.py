import requests

url = "https://popcon.debian.org/by_inst"

r = requests.get(url)

lines = r.text.splitlines()

packages = []

for line in lines:
    if line.startswith("#") or not line.strip():
        continue

    parts = line.split()

    if len(parts) >= 3:
        name = parts[2]
        packages.append(name)

    if len(packages) == 10:
        break

print("Top 10 Debian packages:")

for pkg in packages:
    print("-", pkg)
