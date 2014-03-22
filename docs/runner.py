#!/usr/bin/python3

from optparse import OptionParser
from os import path, times
from subprocess import Popen, PIPE
from threading import Thread
from itertools import product

class Field(object):
	DRAW = 0
	WHITE = 1
	BLACK = 2

	def __init__(self):
		super(Field, self).__init__()
		self.counters = [0, 0, 0, 0, 0, 0, 0]
		self.history = []
		self.field = [
			[0, 0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0, 0],
			[0, 0, 0, 0, 0, 0, 0],
		]

	def make_turn(self, column):
		if self.size() % 2 == 0:
			self.make_turn_impl(column, self.WHITE)
		else:
			self.make_turn_impl(column, self.BLACK)
		self.history.append(column)

	def make_turn_impl(self, column, mark):
		if self.counters[column] >= 6:
			raise Exception("cannot go to " + str(column))
		self.field[self.counters[column]][column] = mark
		self.counters[column] += 1

	def size(self):
		return sum(self.counters)

	def finish(self):
		return self.size() == 42 or self.winner() != 0

	def winner(self):
		def diag1(r, c):
			return [(r, c), (r + 1, c + 1), (r + 2, c + 2), (r + 3, c + 3)]
		def diag2(r, c):
			return [(r, c), (r - 1, c + 1), (r - 2, c + 2), (r - 3, c + 3)]
		def vert(r, c):
			return [(r, c), (r + 1, c), (r + 2, c), (r + 3, c)]
		def horiz(r, c):
			return [(r, c), (r, c + 1), (r, c + 2), (r, c + 3)]

		lines = [diag1(r, c) for r, c in product([0, 1, 2], [0, 1, 2, 3])] + [diag2(r, c) for r, c in product([3, 4, 5], [0, 1, 2, 3])] + [vert(r, c) for r, c in product([0, 1, 2], [0, 1, 2, 3, 4, 5, 6])] + [horiz(r, c) for r, c in product([0, 1, 2, 3, 4, 5], [0, 1, 2, 3])]

		for line in lines:
			marks = set(map(lambda p: self.field[p[0]][p[1]], line))
			if len(marks) == 1 and self.WHITE in marks:
				return self.WHITE
			elif len(marks) == 1 and self.BLACK in marks:
				return self.BLACK

		return self.DRAW


class Game(object):
	def __init__(self, white, black, timeout):
		super(Game, self).__init__()
		self.field = Field()
		self.bot = {"white" : white, "black" : black }
		self.time = {"white" : float(timeout), "black" : float(timeout) }

	def move_impl(self, name, turn):
		start = times()[4]
		turn = self.bot[name].turn(turn + "\n", self.time[name])
		end = times()[4]
		elapsed = end - start
		self.time[name] = self.time[name] - elapsed
		if self.time[name] <= 0:
			return (False, turn, "timeout")
		try:
			self.field.make_turn(int(turn))
		except Exception as err:
			return (False, turn, str(err))

		return (True, turn, "Ok")

	def white_move(self, turn):
		return self.move_impl("white", turn)

	def black_move(self, turn):
		return self.move_impl("black", turn)

	def play(self):
		(cont, turn, mes) = self.white_move("Go")
		if not cont:
			return (self.field.BLACK, mes, self.field)
		while not self.field.finish():
			(cont, turn, mes) = self.black_move(turn)
			if not cont:
				return (self.field.WHITE, mes, self.field)
			if self.field.finish():
				break
			(cont, turn, mes) = self.white_move(turn)
			if not cont:
				return (self.field.BLACK, mes, self.field)
		return (self.field.winner(), "Ok", self.field)

class GameBot(object):
	def __init__(self, cmd):
		super(GameBot, self).__init__()
		self.process = Popen([cmd], bufsize=1, stdin=PIPE, stdout=PIPE)
		if not (self.process.poll() is None):
			raise Exception("{} terminated unexpectedly".format(cmd))

	def turn(self, arg, timeout):
		def threadfunc(res):
			try:
				self.process.stdin.write(bytes(arg, "utf-8"))
				self.process.stdin.flush()
				res.append(self.process.stdout.readline().decode("utf-8").strip())
			except Exception as err:
				res.append(str(err))
		answer = ""
		try:
			res = []
			thread = Thread(target=threadfunc, args=(res,))
			thread.start()
			thread.join(timeout=timeout)
			if thread.is_alive():
				self.kill()
				thread.join()
			elif res:
				answer = res[0]
		except Exception as err:
			answer = str(err)
		return answer

	def kill(self):
		try:
			self.process.terminate()
		except:
			pass

class Match(object):
	def __init__(self, lhs, rhs, timeout):
		super(Match, self).__init__()
		self.white_cmd = lhs
		self.black_cmd = rhs
		self.timeout = timeout

	def start_bots(self):
		white, black = None, None
		try: white = GameBot(self.white_cmd)
		except Exception as err: pass
		try: black = GameBot(self.black_cmd)
		except Exception as err: pass
		return white, black
	
	def stop_bots(self, white, black):
		try: white.kill()
		except: pass
		try: black.kill()
		except: pass

	def play(self):
		wbot, bbot = self.start_bots()
		(white, black, msg, field) = self.play_game(wbot, bbot)
		self.stop_bots(wbot, bbot)
		return (white, black, msg, field.history)

	def play_game(self, white, black):
		if not white and not black:
			return (0, 0, "DQ", Field())
		if white and not black:
			return (2, 0, "DQ", Field())
		if black and not white:
			return (0, 2, "DQ", Field())

		game = Game(white, black, self.timeout)
		(winner, mes, field) = game.play()

		if winner == field.WHITE:
			return (2, 0, mes, field)
		if winner == field.BLACK:
			return (0, 2, mes, field)
		return (1, 1, mes, field)

class Tournament(object):
	def __init__(self, options):
		super(Tournament, self).__init__()
		self.options = options

	def play(self):
		self.points = { prog : 0 for prog in self.options.programs }
		for first in range(len(self.options.programs)):
			for second in range(first + 1, len(self.options.programs)):
				self.play_match(self.options.programs[first], self.options.programs[second])

		print("final table:")
		print(sorted([(b,p) for b,p in self.points.items()], key=lambda p: p[1]))
	
	def play_match(self, first, second):
		for game in range(self.options.games):
			match = Match(first, second, self.options.timeout)
			(fp, sp, mes, history) = match.play()
			self.points[first] += fp
			self.points[second] += sp
			self.print_game(game, first, second, fp, sp, mes, history)

			match = Match(second, first, self.options.timeout)
			(fp, sp, mes, history) = match.play()
			self.points[first] += sp
			self.points[second] += fp
			self.print_game(game, second, first, fp, sp, mes, history)

	def print_game(self, g, f, s, fp, sp, m, h):
		print("Game {}, bots {}".format(g, [f, s]))
		print("Status {}, score {}:{}".format(m, fp, sp))
		print("Moves {}".format(h))

def make_option_parser():
	parser = OptionParser()
	parser.add_option("-t", "--timeout", action="store", type="int", dest="timeout", default=2)
	parser.add_option("-g", "--games", action="store", type="int", dest="games", default=1)
	parser.add_option("-p", "--program", action="append", type="string", dest="programs")
	return parser

def verify_options(options):
	if not options.programs or len(options.programs) < 2:
		print("Error: at least two programs expected")
		exit()

	noexist = list(filter(lambda f: not path.isfile(f), options.programs))
	if noexist:
		print("Error: {} do not exist".format(noexist))
		exit()

if __name__ == "__main__":
	parser = make_option_parser()
	options, _ = parser.parse_args()
	verify_options(options)
	tourn = Tournament(options)
	tourn.play()
