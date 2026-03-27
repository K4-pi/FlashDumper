def strings(file, string_length=4):

    with open(file, "rb") as f:
        data = f.read()

    from re import compile, findall

    chars = rb"A-Za-z0-9/\-:.,_$%'()[\]<> "
        
    regexp = b'[%s]{%d,}' % (chars, string_length)
    pattern = compile(regexp)

    return pattern.findall(data)

def analyze_file_meta(file_path):
    from os import stat

    return stat(file_path)


