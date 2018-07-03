import json
import logging
import sys

from google.appengine.api import urlfetch
from flask import Flask, request
from google.appengine.ext import ndb

import game
import svg
Game = game.Game

app = Flask(__name__)

from secret import VERIFY_TOKEN, ACCESS_TOKEN, FRANK_ID, LEON_ID
VERIFY_TOKEN = "ccf5247b293d9027863ea880ea0a40d8"
ACCESS_TOKEN = "EAACsJo6iTY0BAPJ0oKWFA0XyDaNUbIh57gmKvJdzniDyt2HTCYivEjoeoFWou4L8CEHLMp3IXRmdXka511ng1ipMIb1oAN6nCgyxFpMmEcNakAGj62B9Mf9O5xzsUKsuj2nyRBZCjxEZBUhXZCqSyRVkuIoTt2xTSGH3eR4LwZDZD"

FRANK_ID = "1915527718468764"
LEON_ID = "1852482611478518"

# some debugging commands
@app.route('/leon/<command>')
def leon_handle(command):
    command = command.replace('+', ' ')
    handle(LEON_ID, command)
    return ""

@app.route('/frank/<command>')
def frank_handle(command):
    command = command.replace('+', ' ')
    handle(FRANK_ID, command)
    return ""

@app.route('/', methods=['GET', 'POST'])
def main():
    # facebook confirmation thing for get requests
    if request.method == 'GET':
        return request.args.get('hub.challenge', "")
    
    # process post request
    data = request.get_json()
    logging.info("Recieve response %s" % json.dumps(data))
    for entry in data["entry"]:
        for message_event in entry["messaging"]:
            sender_id = message_event["sender"]["id"]

            if message_event.get("message"):
                message = message_event["message"]
                if message.get("is_echo"):
                    continue
                message_text = message.get("text", "")
                logging.info("Recieved message %s", message_text)
                handle(sender_id, message_text)

    return ""

def handle(sender_id, m):
    if sender_id == LEON_ID:
        message(FRANK_ID, "Leon: " + m)
    elif sender_id == FRANK_ID:
        message(LEON_ID, "Frank: " + m)
    game = Game.query(ndb.OR(Game.white == sender_id, Game.black == sender_id)).get()
    if m.split()[0].lower() == 'play':
        if game:
            message(sender_id, "You are already in a game!")
            return
        if m.split()[1].lower() == 'white':
            if sender_id == LEON_ID:
                game = Game(white=LEON_ID, white_name="Leon", black=FRANK_ID, black_name="Frank")
            else:
                game = Game(black=LEON_ID, black_name="Leon", white=FRANK_ID, white_name="Frank")
        elif m.split()[1].lower() == 'black':
            if sender_id == FRANK_ID:
                game = Game(white=LEON_ID, white_name="Leon", black=FRANK_ID, black_name="Frank")
            else:
                game = Game(black=LEON_ID, black_name="Leon", white=FRANK_ID, white_name="Frank")
        else:
            import random
            if random.randint(0, 1) == 0:
                game = Game(white=LEON_ID, white_name="Leon", black=FRANK_ID, black_name="Frank")
            else:
                game = Game(black=LEON_ID, black_name="Leon", white=FRANK_ID, white_name="Frank")
        game.put()
        game.send_updates() 
        return

    game = Game.query(ndb.OR(Game.white == sender_id, Game.black == sender_id)).get()
    if game:
        game.handle(sender_id, m)
    else:
        message(sender_id, 'You are not in a game, use "play white/black/random" to start a game!')


def name(user_id):
    # it's just me and leon lol
    pass


def message(recipient_id, message_text):
    logging.info("Sending message to %r: %s", recipient_id, message_text)
    headers = {
        "Content-Type": "application/json"
    }
    message = {"text": message_text}

    raw_data = {
        "recipient": {
            "id": recipient_id
        },
        "message": message,
        "messaging_type": "MESSAGE_TAG",
        "tag": "GAME_EVENT"
    }
    data = json.dumps(raw_data)
    r = urlfetch.fetch("https://graph.facebook.com/v2.6/me/messages?access_token=%s" % ACCESS_TOKEN,
                       method=urlfetch.POST, headers=headers, payload=data)
    if r.status_code != 200:
        logging.error("Error sending message: %r", r.status_code)
        logging.error("%s" % r.__dict__)

def send_image(recipient_id, board, player):
    logging.info("Sending image to %r", recipient_id)
    headers = {
        "Content-Type": "application/json"
    }
    message = {
        "attachment": {
            "type": "image",
            "payload": {}
        }
    }

    from poster.encode import multipart_encode, MultipartParam

    payload  = []
    payload.append(MultipartParam('recipient', '{"id":"%s"}' % recipient_id))
    payload.append(MultipartParam('message', json.dumps(message)))
    pic = svg.png_board(board, player)
    payload.append(MultipartParam('filedata', filename="test.png", filetype='image/png', fileobj=pic))
    payload.append(MultipartParam('messaging_type', 'MESSAGE_TAG'))
    payload.append(MultipartParam('tag', 'GAME_EVENT'))

    
    data = multipart_encode(payload)

    r = urlfetch.fetch("https://graph.facebook.com/v2.6/me/messages?access_token=%s" % ACCESS_TOKEN,
                       method=urlfetch.POST, headers=data[1], payload="".join(data[0]))
    if r.status_code != 200:
        logging.error("Error sending svg: %r", r.status_code)
        logging.error("%s" % r.__dict__)
    
