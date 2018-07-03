import chess
from chess.svg import PIECES, CHECK_GRADIENT
import chess.svg
import collections
import math

import xml.etree.ElementTree as ET
from PIL import Image, ImageFont, ImageDraw

def piece_to_png(size):
    from cairosvg import svg2png
    for k,v in PIECES.items():
        svg2png(bytestring=chess.svg.piece(chess.Piece.from_symbol(k)), parent_width=size, write_to='png/' + k + str(size) + '.png')

def check_to_png(size):
    from cairosvg import svg2png
    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "xmlns:xlink": "http://www.w3.org/1999/xlink",
        "width": "45",
        "height": "45"
    })
    defs = ET.SubElement(svg, "defs")
    defs.append(ET.fromstring(CHECK_GRADIENT))
    ET.SubElement(svg, "rect", {
        "x": "0",
        "y": "0",
        "width": "45",
        "height": "45",
        "class": "check",
        "fill": "url(#check_gradient)",
    })
    s = ET.tostring(svg).decode("utf-8")
    svg2png(bytestring=s, parent_width=size, write_to='png/check.png')

# this draws a 400x400 board because dealing with fonts is too hard otherwise
# draw_board(True) draws the board from white's perspective
# draw_board(False) draws the board from black's perspective
def draw_board(side):
    b = Image.new("RGB", (400, 400), color="white")
    draw = ImageDraw.Draw(b)
    font = ImageFont.truetype("Cantarell-Bold.otf", 15)
    for i in range(0, 8):
        
        # draw the numbers
        t = str(8-i) if side else str(i+1)
        w,h = draw.textsize(t)
        # magic numbers, they make everything work out, do not question
        # left side
        draw.text((9-w/2, 39+i*45-h/2), t, font=font, fill="black")
        # right side
        draw.text((389-w/2, 39+i*45-h/2), t, font=font, fill="black")
        
        # draw the letters
        t = chr(ord('a')+i) if side else chr(ord('h')-i)
        w,h = draw.textsize(t)
        
        # shift some letters up/down to make things look better
        #         a  b  c  d  e  f   g  h
        offset = [0, 1, 0, 1, 0, 1, -1, 1]
        if not side:
            # cause letters are in reverse order
            offset.reverse()
        
        # more magic numbers don't question
        draw.text((45+i*45-h/2, 3-w/2 + offset[i]), t, font=font, fill="black")
        draw.text((45+i*45-h/2, 383-w/2 + offset[i]), t, font=font, fill="black")

    for i in range(0, 8):
        for j in range(0, 8):
            if (i + j) % 2 == 0:
                color = "#ffce9e"
            else:
                color = "#d18b47"
            draw.rectangle([20+i*45, 20+j*45, 64+i*45, 64+j*45], fill=color)
    del draw

    filename = "png/board_white.png" if side else "png/board_black.png"
    with open(filename, "wb+") as f:
        b.save(f, "PNG")
    

def png_board(board, player):
    if player == "b":
        flipped = True
    elif player == "w":
        flipped = False
    else:
        raise ValueError("Expected player to be 'b' or 'w'")

    if flipped:
        f = Image.open("png/board_black.png")
    else:
        f = Image.open("png/board_white.png")

    draw = ImageDraw.Draw(f)

    white_check = False
    black_check = False

    if board.is_check():
        if board.turn:
            white_check = True
        else:
            black_check = True

    for square in range(64):
        file_index = chess.square_file(square)
        rank_index = chess.square_rank(square)

        x = (file_index if not flipped else 7 - file_index) * 45 + 20
        y = (7 - rank_index if not flipped else rank_index) * 45 + 20


        if board.move_stack:
            last_move = board.move_stack[-1]
            if square in [last_move.from_square, last_move.to_square]:
                if (file_index + rank_index) % 2 == 0:
                    color = "#aaa23b"
                else:
                    color = "#cdd16a"
                draw.rectangle([x, y, x+44, y+44], fill=color)

        piece = board.piece_at(square)

        if piece:
            if (str(piece) == 'K' and white_check) or (str(piece) == 'k' and black_check):
                check = Image.open("png/check.png")
                f.paste(check, (x,y), check)
                
            piece_png = "png/" + str(piece) + "45.png"
            m = Image.open(piece_png)
            f.paste(m, (x,y), m)

    del draw

    import StringIO
    output = StringIO.StringIO()
    f.save(output, "PNG")
    return output
