import python_obfuscator

# TODO: Improve tests
def test_module_methods():
    obfuscate = python_obfuscator.obfuscator()

    code = """
    def add(x, y):
    \treturn x+y
    assert add(10,10) == 20
    assert add(0,0) == 0
    """.replace(
        "    ", ""
    )

    exec(obfuscate.obfuscate(code))
