import chess
import chess.uci
import engine as e
import time
import os


class PerftSuite():
    def __init__(self):
        self.depth = 3
        self.positions = []

    def parse(self, params):
        for p in params:
            words = p.split('=')

            if words[0] == "suite":
                self.suite_path = words[1]
            elif words[0] == "depth":
                self.depth = words[1]
            elif words[0] == "engine":
                self.engine_path = words[1]
            else:
                print("Warning: Unknown parameter {}".format(words[0]))

    def run(self, verbose=False):
        if os.path.isdir(self.suite_path):
            directory = self.suite_path
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.epd'):
                        self.load(directory + file)
                        self.start(self.engine_path, depth=self.depth)
                        self.results()
                        print("")
        else:
            self.load(self.suite_path)
            self.start(self.engine_path, depth=self.depth)
            self.results()

    def load(self, path):
        self.positions = []

        file = open(path, 'r')
        for line in file:
            if len(line) < 3 or line[0] == '#':
                continue

            line = line.rstrip('\n')
            words = line.split(';')

            # Try filter out non-fen strings
            if words[0].count('/') != 7:
                continue

            # Test FEN
            try:
                board = chess.Board(words[0])
            except ValueError:
                print("Invalid FEN: {}".format(words[0]))
                continue

            # Parse answers
            answers = []
            for word in words[1:]:
                subwords = word.split(' ')
                subwords.remove('')
                answers.append([subwords[1], subwords[2]])

            # Add FEN and answers
            self.positions.append([words[0], answers])
        self.suite_path = path

    def start(self, engine_path, depth=3, verbose=False):
        engine = chess.uci.popen_engine(engine_path, engine_cls=e.MyEngine)
        engine.uci()
        engine.isready()
        self.wrong = 0

        t0 = time.time()
        for pos in self.positions:
            board = chess.Board(pos[0])
            engine.position(board)

            answers = pos[1]
            results = engine.perft(depth)

            # Check answers
            for a, r in zip(answers, results):
                if a[1] != r[1]:
                    self.wrong += 1
                    if verbose:
                        print("FEN {} expected {} got {}".format(pos[0], a[1], r[1]))
                    break
        t1 = time.time()

        engine.stop()
        engine.quit()

        # Save results
        self.total = len(self.positions)
        self.right = self.total-self.wrong
        self.time_used = t1 - t0
        self.depth = depth

    def results(self):
        print("Engine: {}".format(self.engine_path))
        print("Suite:  {}".format(self.suite_path))
        print("Pass:   {}/{} ({:.1f}%)".format(self.right, self.total, 100*self.right/self.total))
        print("Fail:   {}/{} ({:.1f}%)".format(self.wrong, self.total, 100*self.wrong/self.total))
        print("Depth:  {}".format(self.depth))
        print("Time:   {:.2f}s".format(self.time_used))
