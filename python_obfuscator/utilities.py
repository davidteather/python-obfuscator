import re
import ast
import random
import time
from .helpers import VariableNameGenerator, RandomDataTypeGenerator
import regex

def one_liner(code):
    return """exec(\"\"\"{}\"\"\")""".format(code.replace("\n", ";").replace('"""', '\\"\\"\\"'))

def variable_renamer(code):
    variable_names = re.findall(r"(\w+)(?=( |)=( |))", code)
    name_generator = VariableNameGenerator()
    for i in range(len(variable_names)):
        obfuscated_name = name_generator.get_random(i+1)
        code = re.sub(r"\b(" + variable_names[i][0] + r")\b", obfuscated_name, code)

    return code

def add_random_variables(code):
    useless_variables_to_add = random.randint(100,400)
    name_generator = VariableNameGenerator()
    data_generator = RandomDataTypeGenerator()
    for v in range(useless_variables_to_add):
        rand_data = data_generator.get_random()
        if type(rand_data) == str:
            rand_data = '"{}"'.format(rand_data)
        if v % 2 == 0:
            code = "{} = {}\n".format(name_generator.get_random(v), rand_data) + code
        else:
            code = code + "\n{} = {}".format(name_generator.get_random(v), rand_data)
    return code

def str_to_bytes(code):
    # (?<=(( |	|)\w+( |)=( |))("""|"|'))[\W\w]*?(?=("""|"|'))
    python_string_decoraters = ['"""', '"', "'"]

    variable_names = []
    for s in python_string_decoraters:
        t = regex.findall(r"(?<=(( |	|\n)\w+( |)=( |))(\"\"\"|\"|'))[\W\w]*?(?=(\"\"\"|\"|'))", code)
        variable_names += t
        print(t)

    print(variable_names)
    raise Exception()
    for name in variable_names:
        var_value = code.split(name + " = ").split("\n")[0]
        if var_value[0] == '"':
            # need to check if """ string
            if var_value[:3] == '"""':
                # is a """ string
                pass
            else:
                var_value
        elif var_value[0] == "'":
            pass
    return code

def obfuscate(code, remove_techniques=[]):
    if len(remove_techniques) == 0:
        methods = all_methods
    else:
        methods = all_methods.copy()
        for technique in remove_techniques:
            methods.remove(technique)

    for technique in methods:
        code = technique(code)

    return code

all_methods = [str_to_bytes, variable_renamer, add_random_variables, one_liner]