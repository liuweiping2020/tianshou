import argparse
import sys
import re
import time
import os
from game import Game
from engine import GTPEngine
import utils
from time import gmtime, strftime

python_version = sys.version_info

if python_version < (3, 0):
    import cPickle
else:
    import _pickle as cPickle

class Data(object):
    def __init__(self):
        self.boards = []
        self.probs = []
        self.winner = 0

    def reset(self):
        self.__init__()


if __name__ == '__main__':
    """
    Starting two different players which load network weights to evaluate the winning ratio.
    Note that, this function requires the installation of the Pyro4 library.
    """
    # TODO : we should set the network path in a more configurable way.
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", type=str, default="./data/")
    parser.add_argument("--black_weight_path", type=str, default=None)
    parser.add_argument("--white_weight_path", type=str, default=None)
    parser.add_argument("--debug", type=bool, default=False)
    parser.add_argument("--game", type=str, default="go")
    args = parser.parse_args()

    if not os.path.exists(args.data_path):
        os.mkdir(args.data_path)
    # black_weight_path = "./checkpoints"
    # white_weight_path = "./checkpoints_origin"
    if args.black_weight_path is not None and (not os.path.exists(args.black_weight_path)):
        raise ValueError("Can't find the network weights for black player.")
    if args.white_weight_path is not None and (not os.path.exists(args.white_weight_path)):
        raise ValueError("Can't find the network weights for white player.")

    game = Game(name=args.game,
                black_checkpoint_path=args.black_weight_path,
                white_checkpoint_path=args.white_weight_path,
                debug=args.debug)
    engine = GTPEngine(game_obj=game, name='tianshou', version=0)

    data = Data()
    role = ["BLACK", "WHITE"]
    color = ['b', 'w']

    pattern = "[A-Z]{1}[0-9]{1}"
    space = re.compile("\s+")
    size = {"go":9, "reversi":8}
    show = ['.', 'X', 'O']

    evaluate_rounds = 100
    game_num = 0
    try:
        while True:
        #while game_num < evaluate_rounds:
            start_time = time.time()
            num = 0
            pass_flag = [False, False]
            print("Start game {}".format(game_num))
            # end the game if both palyer chose to pass, or play too much turns
            while not (pass_flag[0] and pass_flag[1]) and num < size[args.game] ** 2 * 2:
                turn = num % 2
                board = engine.run_cmd(str(num) + ' show_board')
                board = eval(board[board.index('['):board.index(']') + 1])
                for i in range(size[args.game]):
                    for j in range(size[args.game]):
                        print show[board[i * size[args.game] + j]] + " ",
                    print "\n",
                data.boards.append(board)
                start_time = time.time()
                move = engine.run_cmd(str(num) + ' genmove ' + color[turn])[:-1]
                print("\n" + role[turn] + " : " + str(move)),
                num += 1
                match = re.search(pattern, move)
                if match is not None:
                    # print "match : " + str(match.group())
                    play_or_pass = match.group()
                    pass_flag[turn] = False
                else:
                    # print "no match"
                    play_or_pass = ' PASS'
                    pass_flag[turn] = True
                prob = engine.run_cmd(str(num) + ' get_prob')
                prob = space.sub(',', prob[prob.index('['):prob.index(']') + 1])
                prob = prob.replace('[,', '[')
                prob = prob.replace('],', ']')
                prob = eval(prob)
                data.probs.append(prob)
            score = engine.run_cmd(str(num) + ' get_score')
            print("Finished : {}".format(score.split(" ")[1]))
            if eval(score.split(" ")[1]) > 0:
                data.winner = utils.BLACK
            if eval(score.split(" ")[1]) < 0:
                data.winner = utils.WHITE
            engine.run_cmd(str(num) + ' clear_board')
            file_list = os.listdir(args.data_path)
            current_time = strftime("%Y%m%d_%H%M%S", gmtime())
            if os.path.exists(args.data_path + current_time + ".pkl"):
                time.sleep(1)
                current_time = strftime("%Y%m%d_%H%M%S", gmtime())
            with open(args.data_path + current_time + ".pkl", "wb") as file:
                picklestring = cPickle.dump(data, file)
            data.reset()
            game_num += 1
    except KeyboardInterrupt:
        pass
