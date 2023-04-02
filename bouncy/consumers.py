import json
import random
import string
import time
import asyncio
import math
import random

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from bouncy.models import AvailablePlayer


def random_string(n):
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n))

def find_available_player():
    available_player = AvailablePlayer.objects.first()
    if(available_player):
        available_player_channel_name = available_player.channel_name
        available_player.delete()
        return available_player_channel_name
    return None

def delete_player_from_db(channel_name):
    AvailablePlayer.objects.filter(channel_name = channel_name).delete()

class GameConsumer(AsyncWebsocketConsumer):

    def add_channel_name_to_db(self):
        # Before adding the channel_name, we do a bit of housekeeping. We may sure that the
        # channel_name isn't already on the database due to a glitch.
        AvailablePlayer.objects.filter(channel_name = self.channel_name).delete()
        player = AvailablePlayer(channel_name = self.channel_name)
        player.save()

    async def connect(self):
 
        # We check if there any available players.
        available_player = await sync_to_async(find_available_player)()
        
        if(available_player):
            # This is an indentifier used by channels for game communication.
            self.game_id = random_string(10)

            # Assign red and blue randomly to players.
            (other_color, self.color) = ('red','blue') if random.uniform(0, 1) < 0.5 else ('blue','red')


            print("player 1: " + str(available_player))
            print("player 2: " + str(self.channel_name))
            # Send message to available_player with game_id over channel_layer.
            # The GameConsumer for available_player will receive this data via the start_game function.
            new_game_data_for_available_player = {"type": "start_game",
                                                  "host": self.channel_name,
                                                  "game_id": self.game_id,
                                                  "color": other_color}
            await self.channel_layer.send(available_player, new_game_data_for_available_player);
            self.game_id_name = "game_%s" % self.game_id
            await self.channel_layer.group_add(self.game_id_name, self.channel_name)

            # Accepts all WebSocket traffic from user.
            await self.accept()
    
            # Send message to current_player through WebSocket.
            new_game_data_for_current_player = {"type": "start_game",
                                                "host": self.channel_name,
                                                "game_id": self.game_id,
                                                "color": self.color}
            await self.channel_layer.send(self.channel_name, new_game_data_for_current_player);            
        else:
            # Accepts all WebSocket traffic from user.
            await self.accept()

            # Adds players channel_name to the database.
            await sync_to_async(self.add_channel_name_to_db)()

    async def disconnect(self, close_code):
        await sync_to_async(delete_player_from_db(self.channel_name))
        await self.channel_layer.group_discard(self.game_id_name, self.channel_name)
    
    # This function should only be called on the consumer for the player who first arrives
    # at the server. The second player does this setup in the connect function.
    async def start_game(self, game_data):
        self.game_id = game_data["game_id"]
        self.color = game_data["color"]
        self.game_id_name = "game_%s" % game_data['game_id']
        self.host = game_data['host']
        await self.channel_layer.group_add(self.game_id_name, self.channel_name)
        await self.send(text_data=json.dumps(game_data))
            
    async def ball_move(self, ball_data):
        await self.send(text_data=json.dumps(ball_data))

    async def new_ball(self, ball_data):
        print("new ball at (" + str(ball_data['x']) + "," + str(ball_data['y']) + ") of color " + ball_data['color'])
        raw_x = random.random()
        raw_y = random.random()
        dir_x = raw_x/math.sqrt(raw_x**2 + raw_y**2)
        dir_y = raw_y/math.sqrt(raw_x**2 + raw_y**2)
        radius = 10*random.random() + 10
        ball = Ball(ball_data['x'], ball_data['y'], dir_x, dir_y, radius, ball_data['color'])
        self.balls.append(ball)
        
    async def receive(self, text_data):
    
        if(self.host):    
            # data will be a dictionary with and x and y coordinate for where player clicked to place
            # a new ball.
            data = json.loads(text_data)
            
            await self.channel_layer.send(self.host, {"type": "new_ball", 
                                                      "color": self.color,
                                                      "x": data["x"],
                                                      "y": data["y"]})

from channels.consumer import SyncConsumer

class PrintConsumer(SyncConsumer):
    def test_print(self, message):
        print(message)