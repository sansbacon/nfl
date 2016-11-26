#!/usr/bin/python

# A huge thanks to swanson
# this solution is almost wholly based off
# https://github.com/swanson/degenerate

from random import uniform, choice

from ortools.linear_solver import pywraplp

from orm import Player, Roster
from constants import *


'''
Load Salary and Prediction data from csv's
'''
def load_players(players, projection_formula=None, team_exclude=[], player_exclude=[], random=True):
    '''
    Takes list of player dicts, returns list of Player objects
    :param players(list): of player dict
    :return: all_players(list): of Player
    '''
    all_players = []

    for p in players:
        oppos = str(p.get('Opposing_TeamFB', '').replace('@', ''))
        pos = str(p.get('Position'))
        if pos == 'D':
            pos = str('DST')
        team = str(p.get('Team'))
        player_name = str(p.get('Player_Name'))
        code = str('{}_{}'.format(player_name, pos))

        mean_projection = p.get('AvgPts', 0)
        ceiling = p.get('Ceiling', 0)
        floor = p.get('Floor', 0)

        projections = [mean_projection + round(mean_projection * uniform(-.05,.05), 2)]
        ceilings = [ceiling + round(ceiling * uniform(-.05,.05), 3)]
        floors = [floor + round(floor * uniform(-.05,.05), 3)]

        if projection_formula == 'cash':
            proj = (choice(projections) * .5) + (choice(ceilings) * .15) + (choice(floors) * .35)
        elif projection_formula == 'tournament':
            proj = (choice(projections) * .3) + (choice(ceilings) * .6) + (choice(floors) * .1)
        elif projection_formula == 'tourncash':
            proj = (choice(projections) * .4) + (choice(ceilings) * .3) + (choice(floors) * .3)
	elif ',' in projection_formula:
	    avg, ceiling, floor = projection_formula.split(',')
            proj = (choice(projections) * avg) + (choice(ceilings) * ceiling) + (choice(floors) * floor)
        else:
            proj = choice(projections)

        if team in team_exclude:
            continue
        elif player_name in player_exclude:
            continue
        else:
            all_players.append(Player(proj=proj, oppos=oppos, code=code, pos=pos, name=player_name, cost=p.get('Salary'), team=team))

    return all_players

'''
handle or-tools logic
'''
def run_solver(all_players, depth, min_teams=None, stack_wr=None, stack_te=None):
    solver = pywraplp.Solver('FD', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    '''
    Setup Binary Player variables
    '''
    variables = []
    for player in all_players:
        variables.append(solver.IntVar(0, 1, player.code))

    '''
    Setup Maximization over player point projections
    '''
    objective = solver.Objective()
    objective.SetMaximization()
    for i, player in enumerate(all_players):
        objective.SetCoefficient(variables[i], player.proj)
    '''
    Add Salary Cap Constraint
    '''
    salary_cap = solver.Constraint(SALARY_CAP-1000, SALARY_CAP)
    for i, player in enumerate(all_players):
        salary_cap.SetCoefficient(variables[i], player.cost)

    '''
    Add Player Position constraints including flex position
    '''
    flex_rb = solver.IntVar(0, 1, 'Flex_RB')
    flex_wr = solver.IntVar(0, 1, 'Flex_WR')
    flex_te = solver.IntVar(0, 1, 'Flex_TE')

    solver.Add(flex_rb+flex_wr+flex_te==1)

    for position, limit in POSITION_LIMITS_FLEX:
        ids, players_by_pos = zip(*filter(lambda (x,_): x.pos in position, zip(all_players, variables)))
        if position == 'WR':
            solver.Add(solver.Sum(players_by_pos) == limit+flex_wr)
        elif position == 'RB':
            solver.Add(solver.Sum(players_by_pos) == limit+flex_rb)
        elif position == 'TE':
            solver.Add(solver.Sum(players_by_pos) == limit+flex_te)
        else :
            solver.Add(solver.Sum(players_by_pos) == limit)

    '''
    Add min number of different teams players must be drafted from constraint (draftkings == 2)
    '''
    if min_teams:
        team_names = set([o.team for o in all_players])
        teams = []
        for team in team_names:
            teams.append(solver.IntVar(0, 1, team))
        solver.Add(solver.Sum(teams) >= min_teams)

        for idx, team in enumerate(team_names):
            ids, players_by_team = zip(*filter(lambda (x, _): x.team in team, zip(all_players, variables)))
            solver.Add(teams[idx] <= solver.Sum(players_by_team))

    '''
    Add Defence cant play against any offense's player team constraint
    '''
    o_players = filter(lambda x: x.pos in ['QB', 'WR', 'RB', 'TE'], all_players)
    teams_obj = filter(lambda x: x.pos == 'DST', all_players)
    teams = set([o.team for o in teams_obj])
    for opps_team in team_names:
        if opps_team in teams:
            ids, players_by_opps_team = zip(
                *filter(lambda (x, _): x.pos in ['QB', 'WR', 'RB', 'TE'] and x.opps_team in opps_team,
                        zip(all_players, variables)))
            idxs, defense = zip(
                *filter(lambda (x, _): x.pos == 'DST' and x.team in opps_team, zip(all_players, variables)))
            for player in players_by_opps_team:
                solver.Add(player <= 1 - defense[0])

    '''
    Add remove previous solutions constraint and loop to generate X rosters
    '''
    rosters = []
    for x in xrange(depth):
        if rosters :
            ids, players_from_roster = zip(*filter(lambda (x,_): x in rosters[-1].sorted_players()  , zip(all_players, variables)))
            ids, players_not_from_roster = zip(*filter(lambda (x,_): x  not in rosters[-1].sorted_players()  , zip(all_players, variables)))
            solver.Add(solver.Sum(players_not_from_roster)+solver.Sum(1-x for x in players_from_roster)>=9)
        solution = solver.Solve()
        if solution == solver.OPTIMAL:
            roster = Roster()
            for i, player in enumerate(all_players):
                if variables[i].solution_value() == 1:
                    roster.add_player(player)
            rosters.append(roster)
            #print "Optimal roster: %s" % x
            #print roster
        else:
            raise Exception('No solution error')

    return rosters

'''
Main Loop
'''
if __name__ == "__main__":
    import json

    from nfl.parsers.fantasylabs import FantasyLabsNFLParser
    from optimize import load_players, run_solver

    with open('/home/sansbacon/fl_model_11-16-2016_524658.json', 'r') as infile:
        content = json.load(infile)

    rosters = []
    p = FantasyLabsNFLParser()
    players = p.model(content, site='dk')
    player_exclude = ['Jarvis Landry', 'Jordan Matthews', 'Tennessee Defense', 'Alex Smith']
    for x in range(1,11):
        all_players = load_players(players, projection_formula='tourncash',
                                   player_exclude=player_exclude,
                                   team_exclude=['CAR', 'OAK', 'NO', 'HOU'])
        rosters.append(run_solver(all_players, depth=1, stack_wr=True, stack_te=True, min_teams=4))

    print rosters
