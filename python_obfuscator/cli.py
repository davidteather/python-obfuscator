import sys
from .obfuscator import obfuscator
from .utilities import one_liner

def convert_file(file_path):
    obfuscate = obfuscator()

    with open(file_path, 'r') as f:
        data = f.read()
        obfuscated_data = obfuscate.obfuscate(data)

    with open(file_path, 'w+') as f:
        f.write(obfuscated_data)

if __name__ == '__main__':
    python_file = sys.argv[1]
    convert_file(python_file)