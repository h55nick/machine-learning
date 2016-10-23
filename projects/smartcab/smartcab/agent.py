import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator
import random

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        # sets self.env = env, state = None, next_waypoint = None, and a default color
        super(LearningAgent, self).__init__(env)
        self.color = 'green'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
        self.enforce_deadline = True
        self.table = {}
        # recorder helpers
        self.recorder = []
        self.recorder_avgs = []
        self.recorder_t = []
        self.max_success = 0
        # q vars
        self.alpha=0.9
        self.gamma=0.9

    def reset(self, destination=None):
        self.planner.route_to(destination)
        # TODO: Prepare for a new trip; reset any variables here, if required

    def get_traffic_state(self, inputs):
        """
        defines all the traffic violation states, inclusive of multiple
        """
        traffic = ''
        if inputs['oncoming'] != None:
            # to make consistent with next_waypoint output
            traffic = traffic + 'straight'
        if inputs['right'] != None:
            traffic =  traffic + 'right'
        if inputs['left'] != None:
            traffic = traffic + 'left'
        else:
            traffic = ''
        return traffic

    def get_value(self, state, action):
        return self.table.get(state, {}).get(action, 0)

    def max_Q_value(self, state):
        maxQ = 0
        for action in self.env.valid_actions:
            this_value = self.get_value(state, action)
            if this_value > maxQ:
                maxQ = this_value
        return maxQ

    def set_value(self, state, action, reward):
        old_value = self.get_value(state, action)
        new_value = old_value * (1 - self.alpha) + self.alpha * (reward + self.gamma * self.max_Q_value(state=state))
        self.table.get(state, {})[action] = new_value

    def chooseAction(self, state):
        best_actions = []
        maxQ = self.max_Q_value(state)
        for act in self.env.valid_actions:
            if self.get_value(state, act) == maxQ:
               best_actions.append(act)
        return random.choice(best_actions)

    def update_influence_variables(self, t):
        # self.gamma = self.gamma / ln(t)
        self.alpha =  self.alpha / ln(t + 2)
        print('1')

    def avg(self, array):
        return sum(array)/float(len(array))

    def record_results(self, deadline, reward, t):
        print "temp Q-Table {}".format(self.table)
        # if success
        if reward == 12:
            self.recorder.append(1)

        # if fail
        if deadline == 1:
            self.recorder.append(0)

        if reward == 12 or deadline == 1:
            self.recorder_t.append(float(t)/15)
            current_average = self.avg(self.recorder)
            t_average = self.avg(self.recorder_t)
            # to avoid t=1 success skewing.
            if current_average != 1:
                self.recorder_avgs.append(current_average)
                self.max_success = max(self.recorder_avgs)
                max_at = self.recorder_avgs.index(self.max_success)
            print "Success%: {} {}, max: {}, max_trial {}, t-avg, {}".format(len(self.recorder), current_average, self.max_success, max_at, t_average)
            print "Final Q-Table {}".format(self.table)


    def violation_state(self, inputs):
        if inputs['light'] == 'green':
            #  NOTE: no light violation, check traffic.
            return self.get_traffic_state(inputs)
        else:
            # NOTE: red light.
            return 'red'

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        # TODO: Update state
        self.state_hash = {
            'violation': self.violation_state(inputs),
            'next_waypoint': self.next_waypoint,
        }
        self.state = 'violation: {}, next_waypoint: {}'.format(self.state_hash['violation'], self.next_waypoint)
        self.table[self.state] = self.table.get(self.state, {})

        # TODO: Select action according to your policy
        action = self.chooseAction(self.state)
        #random.choice(self.env.valid_actions)

        # Execute action and get reward
        reward = self.env.act(self, action)

        # TODO: Learn policy based on state, action, reward
        self.set_value(self.state, action, reward)

        print "t-{} LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}, next_waypoint = {}, state = {}".format(t, deadline, inputs, action, reward, self.next_waypoint, self.state)  # [debug]

        self.record_results(deadline, reward, t)



def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=True)  # specify agent to track
    # NOTE: You can set enforce_deadline=False while debugging to allow longer trials

    # Now simulate it
    sim = Simulator(e, update_delay=0, display=False)  # create simulator (uses pygame when display=True, if available)
    # NOTE: To speed up simulation, reduce update_delay and/or set display=False

    sim.run(n_trials=100)  # run for a specified number of trials
    # NOTE: To quit midway, press Esc or close pygame window, or hit Ctrl+C on the command-line


if __name__ == '__main__':
    run()
