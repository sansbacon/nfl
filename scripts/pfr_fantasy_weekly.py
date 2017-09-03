import json
import logging


from nfl.scrapers.pfr import PfrNFLScraper
from nfl.parsers.pfr import PfrNFLParser


def _fix_null(k, v):
    if k in ['season_year', 'source_player_id', 'source_player_position']:
        if v == "":
            return None
        else:
            return v
    else:
        return _fix_val(v)


def _fix_val(v):
    try:
        v = float(v)
    except:
        v = 0
    finally:
        return v


def _insp(vals):
    for player in vals:
        p = {k: _fix_null(k, v) for k, v in player.items() if k in wanted}
        p['source'] = 'pfr'
        p['source_team_code'] = player['team']
        p['source_player_name'] = player['player']
        p['fantasy_points_std'] = _fix_val(player['fantasy_points'])
        p['fantasy_points_ppr'] = _fix_val(player['fantasy_points']) + _fix_val(player['rec'])
        p['week'] = player['week_num']
        db._insert_dict(p, 'extra_fantasy.playerstats_fantasy_weekly')



parser = PfrNFLParser()
scraper = PfrNFLScraper(delay=1.5)

wanted = ['season_year', 'source_player_id', 'source_player_position',
          'draftkings_points', 'fanduel_points']

all_players = []
for seas in reversed(range(2009, 2016)):
    for week in range(1, 18):
        for pos in ['QB', 'WR', 'TE', 'RB']:
            content = scraper.playerstats_fantasy_weekly(
                season_year=seas, week=week, pos=pos)
            players = parser.playerstats_fantasy_weekly(
                content, season_year=seas, pos=pos)
            all_players.append(players)
            logging.info('{} finished {} week {} offset 0'.format(seas, pos, week))
            _insp(players)

            if len(players) == 100:
                try:
                    content = scraper.playerstats_fantasy_weekly(
                        season_year=2016, week=week, pos=pos, offset=100)
                    players = parser.playerstats_fantasy_weekly(
                        content, season_year=2016, pos=pos)
                    all_players.append(players)
                    logging.info('finished {} week {} offset 100'.format(pos, week))
                    _insp(players)

                except:
                    pass

with open('/home/sansbacon/all_players.json', 'w') as outfile:
    json.dump(all_players, outfile)