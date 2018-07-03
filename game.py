import chess
import chess.svg

from google.appengine.ext import ndb

import parse
def default_boardstate():
    board = chess.Board()
    return chess._BoardState(board).__dict__

def get_boardstate(data):
    state = chess._BoardState(chess.Board())
    for key, value in data.iteritems():
        setattr(state, key, value)
    return state

def get_move(data):
    move = chess.Move(**data)
    return move

def get_movestack(data):
    return [get_move(x) for x in data]

def get_board_stack(data):
    return [get_boardstate(x) for x in data]

def get_board(move_stack, board_stack, board_state):
    board = chess.Board()
    get_boardstate(board_state).restore(board)
    board.stack = get_board_stack(board_stack)
    board.move_stack = get_movestack(move_stack)
    return board
    

class Game(ndb.Model):
    white_undo = ndb.BooleanProperty(default=False)
    black_undo = ndb.BooleanProperty(default=False)

    white_draw = ndb.BooleanProperty(default=False)
    black_draw = ndb.BooleanProperty(default=False)

    white = ndb.StringProperty(required=True)
    black = ndb.StringProperty(required=True)

    white_name = ndb.StringProperty(required=True)
    black_name = ndb.StringProperty(required=True)

    move_stack = ndb.JsonProperty(required=True, default=[])
    board_stack = ndb.JsonProperty(required=True, default=[])

    board_state = ndb.JsonProperty(required=True, default=default_boardstate())

    def set(self):
        if self.board.is_game_over():
            return
        self.move_stack = [move.__dict__ for move in self.board.move_stack]
        self.board_stack = [board.__dict__ for board in self.board.stack]
        self.board_state = chess._BoardState(self.board).__dict__
        self.put()


    _board = None

    @property
    def board(self):
        if not self._board:
            self._board = get_board(self.move_stack, self.board_stack, self.board_state)
        return self._board

    def send_updates(self):
        from main import send_image, message
        board = chess.svg.board(self.board)
        send_image(self.black, self.board, 'b')
        send_image(self.white, self.board, 'w')
        if self.board.is_game_over():
            if self.board.is_checkmate():
                name = self.black_name if self.board.turn else self.white_name
                message(self.black, "%s wins by checkmate" % name)
                message(self.white, "%s wins by checkmate" % name)

            if self.board.is_stalemate():
                message(self.black, "Stalemate")
                message(self.white, "Stalemate")

            if self.board.is_insufficient_material():
                message(self.black, "Insufficient material")
                message(self.white, "Insufficient material")

            if self.board.is_seventyfive_moves():
                message(self.black, "Draw by 75-move rule")
                message(self.white, "Draw by 75-move rule")

            if self.board.is_fivefold_repetition():
                message(self.black, "Draw by repetition")
                message(self.white, "Draw by repetition")

            self.game_over()
            return


        if self.board.turn:
            message(self.black, "%s to move (White)" % self.white_name)
            message(self.white, "%s to move (White)" % self.white_name)
        else:
            message(self.black, "%s to move (Black)" % self.black_name)
            message(self.white, "%s to move (Black)" % self.black_name)


    def handle(self, player, command):
        from main import message
        if command == "undo":
            if player == self.white:
                self.white_undo = True
            else:
                self.black_undo = True

            if self.white_undo and self.black_undo:
                self.board.pop()
                self.set()
                message(self.black, "Undo successful")
                message(self.white, "Undo successful")
                self.send_updates()
            else:
                if player == self.white:
                    message(self.white, "Requested undo")
                    message(self.black, "%s has requested an undo" % self.white_name)
                else:
                    message(self.black, "Requested undo")
                    message(self.white, "%s has requested an undo" % self.black_name)
            self.put()

        elif command == "resign":
            if player == self.white:
                message(self.white, "You resigned")
                message(self.black, "%s resigned" % self.white_name)
            else:
                message(self.black, "You resigned")
                message(self.white, "%s resigned" % self.black_name)
            self.game_over()
            
        elif command == "draw":
            if self.board.can_claim_draw():
                if player == self.white:
                    message(self.white, "Draw claimed")
                    message(self.black, "%s claimed a draw" % self.white_name)
                else:
                    message(self.black, "Draw claimed")
                    message(self.white, "%s claimed a draw" % self.black_name)

            if player == self.white:
                self.white_draw = True
            else:
                self.black_draw = True

            if self.white_draw and self.black_draw:
                message(self.black, "Draw accepted")
                message(self.white, "Draw accepted")
                self.game_over()
                
            else:
                if player == self.white:
                    message(self.white, "Requested draw")
                    message(self.black, "%s has requested an draw" % self.white_name)
                else:
                    message(self.black, "Requested draw")
                    message(self.white, "%s has requested an draw" % self.black_name)

                self.put()
        else:
            if player != (self.white if self.board.turn else self.black):
                message(player, "It's not your turn!")
                return
            try:
                m = parse.parse_san(self.board, command)
            except ValueError as e:
                if str(e) == "Illegal move.":
                    return
                message(player, str(e))

            self.board.push(m)
            self.send_updates()

            self.white_undo = False
            self.black_undo = False
            self.white_draw = False
            self.black_draw = False
            self.set()

    def game_over(self):
        self.key.delete()




    

