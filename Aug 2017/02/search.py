

lines = []
with open('PR_NODES','rb') as f:
    lines = f.readlines()
for line in lines:
    if line.find('1038937003700') != -1 :
        print line
        break
