filename = "The_Oxford_3000.txt"
out_filename = "The_Oxford_3000.list"

with open(filename, "r") as f:
    content = f.read()
content = content.split("\n")

filtered = filter(lambda line: " " not in line, content)
content = list(filtered)

filtered = filter(lambda line: 3 < len(line) < 11, content)
content = list(filtered)

filtered = filter(lambda line: "-" not in line, content)
content = list(filtered)

filtered = filter(lambda line: "." not in line, content)
content = list(filtered)

filtered = filter(lambda line: "'" not in line, content)
content = list(filtered)

filtered = set([l.lower() for l in content])
content = list(filtered)

with open(out_filename, "w") as f:
    f.write(" ".join(content))
