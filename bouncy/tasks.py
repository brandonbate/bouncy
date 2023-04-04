from celery import shared_task
from time import sleep
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import redis
import pickle
import random
import math

@shared_task
def play(game_id):

    r = redis.Redis()
    channel_layer = get_channel_layer()
    # I make the game_id both the group and channel name. I'm lazy.
    #async_to_sync(channel_layer.group_add)(game_id, game_id)
    balls = []
    

    while(True):
        while(r.exists(game_id)):
            new_ball = pickle.loads(r.lpop(game_id))
            raw_x = random.random()
            raw_y = random.random()
            new_ball['dir_x'] = raw_x/math.sqrt(raw_x**2 + raw_y**2)
            new_ball['dir_y'] = raw_y/math.sqrt(raw_x**2 + raw_y**2)
            new_ball['radius'] = 10*random.random() + 10
            
            balls.append(new_ball)
                        
        sleep(.001)
        
        for i, ball in enumerate(balls):
        			
            # Check if this ball is too close to another ball.
            for j in range(i+1, len(balls)):
            
                other = balls[j]
                dist = math.sqrt((ball['x']-other['x'])**2 + (ball['y']-other['y'])**2)
                dot_prod = ball['dir_x']*(-other['dir_x']) + ball['dir_y']*(-other['dir_y']);
					
                if dist <= ball['radius'] + other['radius']:
                
                    if(ball['radius'] < other['radius']):
                        ball['color'] = other['color']
                    else:
                        other['color'] = ball['color']
						
                    factor_ball = ((ball['dir_x'])*(other['x']-ball['x']) + (ball['dir_y'])*(other['y']-ball['y']))/((other['x']-ball['x'])**2 + (other['y']-ball['y'])**2)                    
                    ball['dir_x'] += (-2)*factor_ball*(other['x'] - ball['x'])
                    ball['dir_y'] += (-2)*factor_ball*(other['y'] - ball['y'])
						
                    factor_other = ((other['dir_x'])*(ball['x']-other['x']) + (other['dir_y'])*(ball['y']-other['y']))/((ball['x']-other['x'])**2 + (ball['y']-other['y'])**2)
                    other['dir_x'] += (-2)*factor_other*(ball['x'] - other['x'])
                    other['dir_y'] += (-2)*factor_other*(ball['y'] - other['y'])
						
            if ball['x'] + ball['radius'] >= 600 and ball['dir_x'] > 0:
                ball['dir_x'] = -ball['dir_x']

            if ball['y']+ball['radius'] >= 400 and ball['dir_y'] > 0:
                ball['dir_y'] = -ball['dir_y']

            if ball['x']-ball['radius'] <= 0 and ball['dir_x'] < 0:
                ball['dir_x'] = -ball['dir_x']

            if ball['y']-ball['radius'] <= 0 and ball['dir_y'] < 0:
                ball['dir_y'] = -ball['dir_y']
            
            ball['x'] = ball['x'] + 0.25*ball['dir_x']
            ball['y'] = ball['y'] + 0.25*ball['dir_y']
    
        async_to_sync(channel_layer.group_send)(game_id,{'type':'game_update', 'data': pickle.dumps(balls)})
