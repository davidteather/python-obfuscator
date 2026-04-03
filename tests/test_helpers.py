"""Tests for helper utilities."""

import random

from python_obfuscator.helpers.random_datatype import RandomDataTypeGenerator
from python_obfuscator.helpers.variable_name_generator import VariableNameGenerator


class TestRandomDataTypeGenerator:
    def test_get_random_returns_str_or_int(self) -> None:
        gen = RandomDataTypeGenerator()
        for _ in range(20):
            assert isinstance(gen.get_random(), (str, int))

    def test_random_string_default_length(self) -> None:
        gen = RandomDataTypeGenerator()
        assert len(gen.random_string()) == 79

    def test_random_string_custom_length(self) -> None:
        gen = RandomDataTypeGenerator()
        assert len(gen.random_string(length=10)) == 10

    def test_random_int_in_valid_range(self) -> None:
        gen = RandomDataTypeGenerator()
        for _ in range(20):
            val = gen.random_int()
            assert isinstance(val, int)
            assert 0 <= val <= 999

    def test_seeded_rng_is_deterministic(self) -> None:
        g1 = RandomDataTypeGenerator(rng=random.Random(42))
        g2 = RandomDataTypeGenerator(rng=random.Random(42))
        results1 = [g1.get_random() for _ in range(10)]
        results2 = [g2.get_random() for _ in range(10)]
        assert results1 == results2

    def test_different_seeds_produce_different_sequences(self) -> None:
        g1 = RandomDataTypeGenerator(rng=random.Random(1))
        g2 = RandomDataTypeGenerator(rng=random.Random(2))
        s1 = [g1.get_random() for _ in range(20)]
        s2 = [g2.get_random() for _ in range(20)]
        assert s1 != s2


class TestVariableNameGenerator:
    def test_get_random_returns_valid_identifier(self) -> None:
        gen = VariableNameGenerator()
        for i in range(1, 15):
            name = gen.get_random(i)
            assert name.isidentifier(), f"{name!r} is not a valid identifier"

    def test_seeded_rng_is_deterministic(self) -> None:
        g1 = VariableNameGenerator(rng=random.Random(42))
        g2 = VariableNameGenerator(rng=random.Random(42))
        names1 = [g1.get_random(i) for i in range(1, 15)]
        names2 = [g2.get_random(i) for i in range(1, 15)]
        assert names1 == names2

    def test_different_seeds_produce_different_names(self) -> None:
        g1 = VariableNameGenerator(rng=random.Random(1))
        g2 = VariableNameGenerator(rng=random.Random(2))
        n1 = [g1.get_random(i) for i in range(1, 15)]
        n2 = [g2.get_random(i) for i in range(1, 15)]
        assert n1 != n2

    def test_individual_generators_return_identifiers(self) -> None:
        gen = VariableNameGenerator(rng=random.Random(0))
        for i in range(1, 10):
            for method in (
                gen.random_string,
                gen.l_and_i,
                gen.time_based,
                gen.just_id,
                gen.scream,
                gen.single_letter_a_lot,
            ):
                name = method(i)
                assert name.isidentifier(), f"{method.__name__}({i}) = {name!r}"
