import random
import string
import time


class RandomDataTypeGenerator:
    def __init__(self):
        self.generator_options = [self.random_string, self.random_int]

    def get_random(self):
        return random.choice(self.generator_options)()

    def random_string(self, length=79):
        # Why is it 79 by default?
        # See: https://stackoverflow.com/a/16920876/11472374
        # As kirelagin commented readability is very important
        return "".join(
            random.choice(string.ascii_lowercase + string.ascii_uppercase)
            for i in range(length)
        )

    def random_int(self):
        return random.randint(random.randint(0, 300), random.randint(300, 999))
