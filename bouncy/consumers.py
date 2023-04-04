import json
import random
import string
import redis
import pickle
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.consumer import SyncConsumer
from bouncy.tasks import play
from bouncy.models import AvailablePlayer
from asgiref.sync import sync_to_async

def find_available_player():
    available_player = AvailablePlayer.objects.first()
    if(available_player):
        available_player_channel_name = available_player.channel_name
        # We remove this player from the database.
        AvailablePlayer.objects.filter(channel_name = available_player_channel_name).delete()

        return available_player_channel_name
    
    return None

def random_string(n):
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n))

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

        # Accepts all WebSocket traffic from user.
        await self.accept()

        # We check if there any available players.
        available_player = await sync_to_async(find_available_player)()
        
        if(available_player):

            # This is an indentifier used by channels for game communication.
            game_id = "game_%s" % random_string(10)
            
            # Assign red and blue randomly to players.
            (available_player_color, current_player_color) = ('red','blue') if random.uniform(0, 1) < 0.5 else ('blue','red')

            print("player 1: " + str(available_player))
            print("player 2: " + str(self.channel_name))

            # Send message to available_player with game_id over channel_layer.
            # The GameConsumer for available_player will receive this data via the start_game function.
            new_game_data_for_available_player = {"type": "start_game",
                                                  "game_id": game_id,
                                                  "color": available_player_color}
            await self.channel_layer.send(available_player, new_game_data_for_available_player)

            # Send message to current_player through WebSocket.
            new_game_data_for_current_player = {"type": "start_game",
                                                "game_id": game_id,
                                                "color": current_player_color}
            await self.channel_layer.send(self.channel_name, new_game_data_for_current_player)
            
            self.host = True
            
            # Queues up celery task.            
            self.task = play.delay(game_id)

        else:

            self.host = False
            
            # Adds players channel_name to the database.
            await sync_to_async(self.add_channel_name_to_db)()

    async def disconnect(self, close_code):
        if(self.host):
            self.task.revoke(terminate=True)

        await self.channel_layer.group_discard(self.game_id, self.channel_name)

    async def start_game(self, data):
        self.r = redis.Redis()

        self.game_id = data['game_id']
        self.color = data['color']
        await self.channel_layer.group_add(self.game_id, self.channel_name)
        await self.send(text_data=json.dumps(data))

	# Receives communication from a celery task.           
    async def game_update(self, data):
        ball_data = pickle.loads(data['data'])
        await self.send(text_data=json.dumps({'type':'game_update', 'ball_data':ball_data}))

    # The only input sent by the user is new ball spawn locations.
    async def receive(self, text_data):
    
        ball_data = json.loads(text_data)
        ball_data['color'] = self.color
            
        # Passes data to the celery task
        self.r.rpush(self.game_id, pickle.dumps(ball_data))

        
