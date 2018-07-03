# Copyright 2012-2018 Niklas Fiekas
# Modified 2018 Frank Dai
# 
# This file is a modified version of the parse_san function from the
# python_chess library. 
# It is modified to accept lowercase piece names, slightly expanded
# castling notations, and modified error messages.
#
# python-chess is copyright (C) 2012-2018 Niklas Fiekas
# <niklas.fiekas@backscattering.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.



from chess import *
import re

SAN_REGEX = re.compile(r"^([nkrqNBKRQ])?([a-h])?([1-8])?[\-x]?([a-h][1-8])(=?[nbrqkNBRQK])?(\+|#)?\Z")

def parse_san(self, san):
    """
    Uses the current position as the context to parse a move in standard
    algebraic notation and returns the corresponding move object.
    The returned move is guaranteed to be either legal or a null move.
    :raises: :exc:`ValueError` if the SAN is invalid or ambiguous.
    """
    # Castling.

    san.replace('0', 'O')
    try:
        if san in ["O-O", "O-O+", "O-O#"]:
            return next(move for move in self.generate_castling_moves() if self.is_kingside_castling(move))
        elif san in ["O-O-O", "O-O-O+", "O-O-O#"]:
            return next(move for move in self.generate_castling_moves() if self.is_queenside_castling(move))
    except StopIteration:
        raise ValueError("Illegal castle.")

    # Match normal moves.
    match = SAN_REGEX.match(san)
    if not match:
        raise ValueError("Invalid move.")

    # Get target square.
    to_square = SQUARE_NAMES.index(match.group(4))
    to_mask = BB_SQUARES[to_square]

    # Get the promotion type.
    p = match.group(5)
    promotion = p and PIECE_SYMBOLS.index(p[-1].lower())

    # Filter by piece type.
    if match.group(1):
        piece_type = PIECE_SYMBOLS.index(match.group(1).lower())
        from_mask = self.pieces_mask(piece_type, self.turn)
    else:
        from_mask = self.pawns

    # Filter by source file.
    if match.group(2):
        from_mask &= BB_FILES[FILE_NAMES.index(match.group(2))]

    # Filter by source rank.
    if match.group(3):
        from_mask &= BB_RANKS[int(match.group(3)) - 1]

    # Match legal moves.
    matched_move = None
    for move in self.generate_legal_moves(from_mask, to_mask):
        if move.promotion != promotion:
            continue

        if matched_move:
            raise ValueError("Ambiguous move.")

        matched_move = move

    if not matched_move:
        if match.group(2) == 'b' and not match.group(1):
            return parse_san(self, "B" + san[1:])
        raise ValueError("Illegal move.")

    return matched_move
