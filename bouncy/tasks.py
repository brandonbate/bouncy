from celery import shared_task
from time import sleep
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task
def play(game_id):

    channel_layer = get_channel_layer()
    # I make the game_id both the group and channel name. I'm lazy.
    async_to_sync(channel_layer.group_add)(game_id, game_id)
    
    
    while(True):
        print("sleep")
        sleep(1)    
        print("sleep done")
        r = async_to_sync(channel_layer.receive)(game_id)
        print("message received:")
        print(r)

	# There needs to be some code here that check if any new balls were spawned.


    #raw_x = random.random()
    #raw_y = random.random()
    #dir_x = raw_x/math.sqrt(raw_x**2 + raw_y**2)
    #dir_y = raw_y/math.sqrt(raw_x**2 + raw_y**2)
    #radius = 10*random.random() + 10

    #i=0
    #    print(i)
    #    sleep(1)
    #    i += 1
    #    async_to_sync(channel_layer.group_send)(
    #        "counter",
    #        {
    #            "type": "number",
    #            "value": i,
    #        },
    #    )
