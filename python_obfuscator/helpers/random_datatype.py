from __future__ import annotations

import random
import string
from typing import Callable


class RandomDataTypeGenerator:
    """Generates random Python literal values (str or int).

    Pass a seeded :class:`random.Random` instance for reproducible output::

        gen = RandomDataTypeGenerator(rng=random.Random(42))
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._generator_options: list[Callable[[], str | int]] = [
            self.random_string,
            self.random_int,
        ]

    def get_random(self) -> str | int:
        return self._rng.choice(self._generator_options)()

    def random_string(self, length: int = 79) -> str:
        # 79 chars: see https://stackoverflow.com/a/16920876/11472374
        return "".join(
            self._rng.choice(string.ascii_lowercase + string.ascii_uppercase)
            for _ in range(length)
        )

    def random_int(self) -> int:
        return self._rng.randint(self._rng.randint(0, 300), self._rng.randint(300, 999))
