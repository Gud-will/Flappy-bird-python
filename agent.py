import torch
import numpy as np
import random
from flappy import FlappyGameAi
from collections import deque
from model import Linear_QNet,QTrainer
from helper import plot

MAX_Mem=100000
BATCH_SIZE=1000
LR=0.0001

class Agent:
    def __init__(self) -> None:
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_Mem) # popleft()
        self.model = Linear_QNet(12, 256, 2)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
    
    def get_state(self,game):
        state = [
            game.pipe_group.sprites()[0].rect[0],
            game.pipe_group.sprites()[0].rect[1],
            game.pipe_group.sprites()[0].rect[2],
            game.pipe_group.sprites()[0].rect[3],
            game.pipe_group.sprites()[1].rect[0],
            game.pipe_group.sprites()[1].rect[1],
            game.pipe_group.sprites()[1].rect[2],
            game.pipe_group.sprites()[1].rect[3],
            game.bird_group.sprites()[0].rect[0],
            game.bird_group.sprites()[0].rect[1],
            game.bird_group.sprites()[0].rect[2],
            game.bird_group.sprites()[0].rect[3],
            ]
        return np.array(state, dtype=float)
    
    def remeber(self,state,action,reward,next_state,done):
        self.memory.append((state,action,reward,next_state,done))

    def train_long_mem(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample=random.sample(self.memory,BATCH_SIZE)
        else:
            mini_sample=self.memory

        states,actions,rewards,next_states,dones=zip(*mini_sample)
        self.trainer.train_step(states,actions,rewards,next_states,dones)    

    def train_short_mem(self,state,action,reward,next_state,done):
        self.trainer.train_step(state,action,reward,next_state,done)


    def get_action(self,state):
        #random moves: tradeoff exploration / exploitation
        self.epsilon=80-self.n_games
        final_move=[0,0]
        if random.randint(0,200)<self.epsilon:
            move=random.randint(0,1)
            final_move[move]=1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plot_scores=[]
    plot_mean_scores=[]
    total_score=0
    record=0
    agent=Agent()
    game=FlappyGameAi()
    while True:
        #get old state
        state_old=agent.get_state(game)
        #get move
        final_move=agent.get_action(state_old)
        #perform move and get new state
        reward,done,score=game.play_step(final_move)
        state_new=agent.get_state(game)
        agent.train_short_mem(state_old,final_move,reward,state_new,done)
        #remeber
        agent.remeber(state_old,final_move,reward,state_new,done)
        if done:
            #train long memory experience replay
            game.reset()
            agent.n_games+=1
            agent.train_long_mem()
            if score>record:
                record=score
                #save model
                agent.model.save()
            print('Game',agent.n_games,'Score:',score,'Record:',record)
            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)

if __name__=='__main__':
    train()