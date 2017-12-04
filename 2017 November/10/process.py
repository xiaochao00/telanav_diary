
import re

with open("./uturn_document_tidy.txt",'r') as f:
    lines = f.readlines()
    for line in lines:
        print line.decode("utf-8")[2:].strip()
