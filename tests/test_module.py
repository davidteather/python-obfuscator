import python_obfuscator

# TODO: Improve tests
def test_module_methods():
    obfuscate = python_obfuscator.obfuscator()

    code = """
    v1 = 0
    v2 = 0
    v4 = 10
    assert v4 + v4 == 20
    assert v1 + v2 == 0
    """.replace(
        "    ", ""
    )

    exec(obfuscate.obfuscate(code))
