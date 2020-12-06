import random
import string
import time


class VariableNameGenerator:
    def __init__(self):
        self.generator_options = [
            self.random_string,
            self.l_and_i,
            self.time_based,
            self.just_id,
            self.scream,
            self.single_letter_a_lot,
        ]

    def get_random(self, id):
        return random.choice(self.generator_options)(id)

    def random_string(self, id, length=79):
        # Why is it 79 by default?
        # See: https://stackoverflow.com/a/16920876/11472374
        # As kirelagin commented readability is very important
        return "".join(
            random.choice(string.ascii_letters) for i in range(length)
        ) + str(id)

    def l_and_i(self, id):
        return "".join(random.choice("Il") for i in range(id))

    def time_based(self, id):
        return (
            random.choice(string.ascii_letters)
            + str(time.time()).replace(".", "")
            + str(id)
        )

    def just_id(self, id):
        # python doesn't work with numbers for variable names
        return random.choice(string.ascii_letters) + str(id)

    def scream(self, id):
        return "".join(random.choice("Aa") for i in range(id))

    def single_letter_a_lot(self, id):
        return random.choice(string.ascii_letters) * id
