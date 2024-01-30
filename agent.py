import pickle
import torch
import numpy as np
import random
from flappy import FlappyGameAi
from collections import deque
from model import Linear_QNet,QTrainer
from helper import plot

MAX_Mem=100000
BATCH_SIZE=1000
LR=0.1

class Agent:
    def __init__(self) -> None:
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_Mem) # popleft()
        self.model = Linear_QNet(8, 256, 1)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
    
    def get_state(self,game):
        bird_x =  game.bird_group.sprites()[0].rect[0]+game.bird_group.sprites()[0].rect[2]
        bird_y =  game.bird_group.sprites()[0].rect[1]
        pipe_1_x= game.pipe_group.sprites()[0].rect[0]
        pipe_1_y= game.pipe_group.sprites()[0].rect[1]
        pipe_2_x= game.pipe_group.sprites()[1].rect[0]
        pipe_2_y= game.pipe_group.sprites()[1].rect[1]+game.pipe_group.sprites()[1].rect[3]
        state = [
            bird_y<pipe_1_y,
            bird_y>pipe_2_y,
            bird_x,
            bird_y,
            pipe_1_x,
            pipe_1_y,
            pipe_2_x,
            pipe_2_y
            ]
        return np.array(state)
    
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
        if random.randint(0,200)<self.epsilon:
            move=random.randint(0,1)
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
        return move


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

def train_supervised():
    with open('player_moves.pkl', 'rb') as inp:
        player_action = pickle.load(inp)
        player_state = pickle.load(inp)
        print(len(player_action))
        print(len(player_state))
    # print(player_state[0])
    # print(player_action[0])
    # # plot_scores=[]
    # # plot_mean_scores=[]
    # # total_score=0
    # # record=0
    agent=Agent()
    # player_state=np.array(player_state)
    # temp=torch.tensor(player_state, dtype=torch.float)
    # temp2=torch.tensor(player_action, dtype=torch.float)
    # print(torch.sum(temp2))
    # print("action",torch.sum(torch.sigmoid(agent.model(temp).squeeze())))
    # # game=FlappyGameAi()
    for epoch in range(10000):
        agent.trainer.train_supervised(player_state,player_action)
    agent.model.save()
    # for player_action in player_action_copy:
    #     #get old state
    #     # state_old=agent.get_state(game)
    #     #get move
    #     player_state=player_action[:-1]
    #     final_move=agent.get_action(player_state)
    #     #perform move and get new state
    #     # reward,done,score=game.play_step(final_move)
    #     # state_new=agent.get_state(game)
    #     # agent.train_short_mem(state_old,final_move,reward,state_new,done)
    #     # #remeber
    #     # agent.remeber(state_old,final_move,reward,state_new,done)
    #     if done:
    #         #train long memory experience replay
    #         game.reset()
    #         agent.n_games+=1
    #         agent.train_long_mem()
    #         if score>record:
    #             record=score
    #             #save model
    #             agent.model.save()
    #         print('Game',agent.n_games,'Score:',score,'Record:',record)
    #         plot_scores.append(score)
    #         total_score += score
    #         mean_score = total_score / agent.n_games
    #         plot_mean_scores.append(mean_score)
    #         plot(plot_scores, plot_mean_scores)

if __name__=='__main__':
    train_supervised()