#For reference

import dis

filename = "main.py"

with open(filename, "r") as f:
    source_code = f.read()

# Compile the source into a code object
code_obj = compile(source_code, filename, "exec")

# Disassemble the whole thing
dis.dis(code_obj)

import dis, marshal

# For Python 3.7+, skip first 16 bytes of the header
with open("__pycache__/main.cpython-314.pyc", "rb") as f:
    f.seek(16) 
    code_obj = marshal.load(f)
    dis.dis(code_obj)