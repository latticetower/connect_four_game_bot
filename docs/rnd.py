#!/usr/bin/python3

import random

class Field(object):
    WHITE = 1
    BLACK = 2

    def __init__(self):
        super(Field, self).__init__()
        self.clear()

    def possible_turns(self):
        return [c for c in range(7) if self.column_size(c) < 6]

    def make_turn(self, column):
        if column not in self.possible_turns():
            raise IndexError(column)
        if self.size() % 2 == 0:
            self.make_turn_impl(column, self.WHITE)
        else:
            self.make_turn_impl(column, self.BLACK)

    def get_lines(self):
        return self.lines

    def empty(self):
        return sum(self.bottoms) == 0

    def column_size(self, column):
        return self.bottoms[column]

    def size(self):
        return sum(self.column_size(c) for c in range(7))

    def clear(self):
        self.bottoms = [0, 0, 0, 0, 0, 0, 0]
        self.field = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]
        ]

    def make_turn_impl(self, column, mark):
        self.field[self.bottoms[column]][column] = mark
        self.bottoms[column] += 1

def random_turn(field):
	return random.choice(field.possible_turns())

field = Field()
try:
	turn = input()
	if turn == "Go":
		while True:
			turn = random_turn(field)
			print(turn)
			field.make_turn(turn)
			turn = int(input())
			field.make_turn(turn)
	else:
		while True:
			field.make_turn(int(turn))
			turn = random_turn(field)
			print(turn)
			field.make_turn(turn)
			turn = int(input())
except Exception as err:
	print(err)
