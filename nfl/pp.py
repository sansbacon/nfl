# -*- coding: utf-8 -*-
'''

# pp.py
# classes to scrape and parse plyr proflr dot com

'''

import json
import logging

from sportscraper.scraper import RequestScraper


class Scraper(RequestScraper):
    """
    For use by subscribers

    """

    @property
    def base_url(self):
        return "https://www.playerprofiler.com/wp-admin/admin-ajax.php?"

    def player_articles(self, site_player_id):
        """
        Gets single player article page from playerprofiler

        Args:
            site_player_id(str):

        Returns:
            dict

        """
        params = {"action": "playerprofiler_articles", "player_id": site_player_id}
        return self.get_json(self.base_url, params=params)

    def player_news(self, site_player_id):
        """
        Gets single player news page from playerprofiler

        Returns:
            dict

        """
        params = {"action": "integrated_news", "player_id": site_player_id}
        return self.get_json(self.base_url, params=params)

    def player_page(self, site_player_id):
        """
        Gets single player page from playerprofiler

        Returns:
            dict

        """
        params = {
            "action": "playerprofiler_api",
            "endpoint": f"/player/{site_player_id}",
        }
        return self.get_json(self.base_url, params=params)

    def players(self):
        """
        Gets list of players, with ids, from playerprofiler

        Returns:
            dict

        """
        params = {"action": "playerprofiler_api", "endpoint": "/players"}
        return self.get_json(self.base_url, params=params)

    def rankings(self):
        """
        Gets current season, dynasty, and weekly rankings from playerprofiler

        Returns:
            dict

        """
        params = {"action": "playerprofiler_api", "endpoint": "/player-rankings"}
        return self.get_json(self.base_url, params=params)


class Parser(object):
    """
    Takes json from scraper, returns list of dict

    """

    def __init__(self):
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    def player_college_performance(self, data):
        """
        Takes player dict, returns college performance

        Args:
            player: dict

        Returns:
            dict

        """
        context = {}
        player = {"site": "playerprofiler", "site_player_id": data["Player_ID"]}
        context.update(player)
        cp_mapping = {
            "College YPC": "college_ypc",
            "College Target Share Rank": "college_target_share_rank",
            "College YPR": "college_ypr",
            "College Dominator Rating Rank": "college_dominator_rating_rank",
            "Breakout Year": "breakout_year",
            "College YPC Rank": "college_ypc_rank",
            "College YPR Rank": "college_ypr_rank",
            "Breakout Age": "breakout_age",
            "College Target Share": "college_target_share",
            "Breakout Age Rank": "breakout_age_rank",
            "College Dominator Rating": "college_dominator_rating",
        }
        cp = {
            cp_mapping[k]: v
            for k, v in data["College Performance"].items()
            if k in cp_mapping.keys()
        }
        context.update(cp)
        return context

    def player_core(self, data):
        """
        Takes player dict, returns core

        Args:
            player:

        Returns:
            dict

        """
        context = {}
        player = {"site": "playerprofiler", "site_player_id": data["Player_ID"]}
        context.update(player)
        core_mapping = {
            "ADP": "adp",
            "ADP Trend": "adp_trend",
            "ADP Year": "adp_year",
            "Height": "height",
            "Height (Inches)": "height_inches",
            "Weight": "weight",
            "Weight Raw": "weight_raw",
            "BMI": "bmi",
            "BMI Rank": "bmi_rank",
            "Hand Size": "hand_size",
            "Hand Size Rank": "hand_size_rank",
            "Arm Length": "arm_length",
            "Arm Length Rank": "arm_length_rank",
            "College": "college",
            "Draft Year": "draft_year",
            "Draft Pick": "draft_pick",
            "Birth Date": "birth_date",
            "Age": "age",
            "Quality Score": "quality_score",
            "Quality Score Rank": "quality_score_rank",
            "Position": "position",
        }
        core = {
            core_mapping[k]: v
            for k, v in data["Core"].items()
            if k in core_mapping.keys()
        }
        context.update(core)

        ## Core has nested data as well
        try:
            context["site_team_name"] = \
                data["Core"]["Team"]["Name"]
        except (ValueError, KeyError):
            pass
        try:
            context["site_team_id"] = \
                data["Core"]["Team"]["Team_ID"]
        except (ValueError, KeyError):
            pass
        try:
            context["best_comparable"] = \
                data["Core"]["Best Comparable Player"]["Player_ID"]
        except (ValueError, KeyError):
            pass
        return context

    def player_game_logs(self, data):
        """
        Takes player data, returns gamelogs

        Args:
            data:

        Returns:
            list of dict

        """
        logs = []
        gl_mapping = {
            "Carries": "carries",
            "Completion Percentage": "completion_percentage",
            "Evaded Tackles": "evaded_tackles",
            "Fantasy Points": "fantasy_points",
            "Interceptions": "interceptions",
            "Opponent": "opponent",
            "Opportunity Share": "opportunity_share",
            "Pass Attempts": "pass_attempts",
            "Passing Touchdowns": "passing_touchdowns",
            "Passing Yards": "passing_yards",
            "Passing Yards Per Attempt": "passing_yards_per_attempt",
            "Receiving Yards": "receiving_yards",
            "Receptions": "receptions",
            "Red Zone Opportunities": "red_zone_opportunities",
            "Red Zone Targets": "red_zone_targets",
            "Rushing Touchdowns": "rushing_touchdowns",
            "Rushing Yards": "rushing_yards",
            "Snap Share": "snap_share",
            "Target Share": "target_share",
            "Targets": "targets",
            "Total Touchdowns": "total_touchdowns",
            "Total Yards": "total_yards",
            "Yards Per Opportunity": "yards_per_opportunity",
            "Yards Per Target": "yards_per_target",
        }

        for seas, seaslog in data["Game Logs"].items():
            for week, log in seaslog.items():
                context = {}
                player = {
                    "season_year": seas,
                    "week": week,
                    "site": "playerprofiler",
                    "site_player_id": data["Player_ID"],
                }
                context.update(player)
                gl = {
                    gl_mapping[k]: v for k, v in log.items() if k in gl_mapping.keys()
                }
                context.update(gl)
                logs.append(context)

        return logs

    def player_medical_history(self, data):
        """
        Takes player data, returns medical history

        Args:
            data:

        Returns:
            list of dict

        """
        histories = []
        mh_mapping = {
            "Games Missed": "games_missed",
            "Games On Injury Report": "games_on_injury_report",
            "Incident Date": "incident_date",
            "Injury Description": "injury_description",
            "Recovery Timetable": "recovery_timetable",
            "Severity": "severity",
            "Surgery": "surgery",
            "Team": "team",
        }

        for seas, seaslog in data["Medical History"].items():
            for injury in seaslog:
                context = {}
                player = {
                    "season_year": seas,
                    "site": "playerprofiler",
                    "site_player_id": data["Player_ID"],
                }
                context.update(player)
                mh = {
                    mh_mapping[k]: v
                    for k, v in injury.items()
                    if k in mh_mapping.keys()
                }
                context.update(mh)
                histories.append(context)

        return histories

    def player_performance_metrics(self, data):
        """
        Takes player dict, returns performance metrics

        Args:
            player:

        Returns:
            dict

        """
        context = {}
        player = {"site": "playerprofiler", "site_player_id": data["Player_ID"]}
        context.update(player)

        # Workout Metrics
        pm_mapping = {
            "ADP": "adp",
            "ADP Trend": "adp_trend",
            "Air Yards": "air_yards",
            "Air Yards Per Attempt": "air_yards_per_attempt",
            "Air Yards Per Attempt Rank": "air_yards_per_attempt_rank",
            "Air Yards Rank": "air_yards_rank",
            "Attempts Per Game": "attempts_per_game",
            "Carries": "carries",
            "Carries Per Game": "carries_per_game",
            "Carries Per Game Rank": "carries_per_game_rank",
            "Carries Rank": "carries_rank",
            "Completion Percentage": "completion_percentage",
            "Completion Percentage Rank": "completion_percentage_rank",
            "Deep Ball Attempts": "deep_ball_attempts",
            "Deep Ball Attempts Per Game": "deep_ball_attempts_per_game",
            "Deep Ball Attempts Rank": "deep_ball_attempts_rank",
            "Deep Ball Completion Percentage": "deep_ball_completion_percentage",
            "Deep Ball Completion Percentage Rank": "deep_ball_completion_percentage_rank",
            "Dropbacks": "dropbacks",
            "Fantasy Points Per Attempt": "fantasy_points_per_attempt",
            "Fantasy Points Per Drop Back": "fantasy_points_per_drop_back",
            "Fantasy Points Per Drop Back Rank": "fantasy_points_per_drop_back_rank",
            "Fantasy Points Per Game": "fantasy_points_per_game",
            "Fantasy Points Per Game Differential": "fantasy_points_per_game_differential",
            "Fantasy Points Per Game Rank": "fantasy_points_per_game_rank",
            "Games": "games",
            "Interceptions": "interceptions",
            "Offensive Line": "offensive_line",
            "Offensive Line Rank": "offensive_line_rank",
            "Pass Attempts Rank": "pass_attempts_rank",
            "Passer Rating": "passer_rating",
            "Passer Rating Rank": "passer_rating_rank",
            "Passing Attempts": "passing_attempts",
            "Passing Touchdowns": "passing_touchdowns",
            "Passing Touchdowns Rank": "passing_touchdowns_rank",
            "Passing Yards": "passing_yards",
            "Passing Yards Per Attempt": "passing_yards_per_attempt",
            "Passing Yards Per Attempt Rank": "passing_yards_per_attempt_rank",
            "Passing Yards Per Game": "passing_yards_per_game",
            "Passing Yards Rank": "passing_yards_rank",
            "Production Premium": "production_premium",
            "Production Premium Rank": "production_premium_rank",
            "Receiver Efficiency": "receiver_efficiency",
            "Receiver Efficiency Rank": "receiver_efficiency_rank",
            "Red Zone Attempts": "red_zone_attempts",
            "Red Zone Attempts Per Game": "red_zone_attempts_per_game",
            "Red Zone Attempts Rank": "red_zone_attempts_rank",
            "Red Zone Carries": "red_zone_carries",
            "Red Zone Carries Per Game": "red_zone_carries_per_game",
            "Red Zone Carries Per Game Rank": "red_zone_carries_per_game_rank",
            "Red Zone Carries Rank": "red_zone_carries_rank",
            "Red Zone Completion Percentage": "red_zone_completion_percentage",
            "Red Zone Completion Percentage Rank": "red_zone_completion_percentage_rank",
            "Rush Yards Per Game": "rush_yards_per_game",
            "Rush Yards Per Game Rank": "rush_yards_per_game_rank",
            "Rushing Touchdowns": "rushing_touchdowns",
            "Rushing Touchdowns Rank": "rushing_touchdowns_rank",
            "Rushing Yards": "rushing_yards",
            "Rushing Yards Rank": "rushing_yards_rank",
            "Sacks": "sacks",
            "Snap Share": "snap_share",
            "Snap Share Rank": "snap_share_rank",
            "Team Pass Plays": "team_pass_plays",
            "Team Pass Plays Rank": "team_pass_plays_rank",
            "Total Fantasy Points": "total_fantasy_points",
            "Total QBR": "total_qbr",
            "Total QBR Rank": "total_qbr_rank",
            "Upcoming Schedule Strength": "upcoming_schedule_strength",
            "Upcoming Schedule Strength Rank": "upcoming_schedule_strength_rank",
            "VOS": "vos",
            "VOS Rank": "vos_rank",
            "Weekly Volatility": "weekly_volatility",
            "Weekly Volatility Rank": "weekly_volatility_rank",
        }
        pm = {
            pm_mapping[k]: v
            for k, v in data["Performance Metrics"].items()
            if k in pm_mapping.keys()
        }
        context.update(pm)
        return pm

    def player_workout_metrics(self, data):
        """
        Takes player dict, returns workout metrics

        Args:
            player:

        Returns:
            dict

        """
        context = {}
        player = {"site": "playerprofiler", "site_player_id": data["Player_ID"]}
        context.update(player)

        # Workout Metrics
        wm_mapping = {
            "20-Yard Shuttle": "20-yard_shuttle",
            "3-Cone Drill": "3-cone_drill",
            "3-Cone Drill Rank": "3-cone_drill_rank",
            "40-Yard Dash": "40-yard_dash",
            "40-Yard Dash Rank": "40-yard_dash_rank",
            "Agility Score": "agility_score",
            "Agility Score Rank": "agility_score_rank",
            "Athleticism Score": "athleticism_score",
            "Athleticism Score Rank": "athleticism_score_rank",
            "Broad Jump": "broad_jump",
            "Broad Jump Rank": "broad_jump_rank",
            "Burst Score": "burst_score",
            "Burst Score Rank": "burst_score_rank",
            "SPARQ-x": "sparq-x",
            "SPARQ-x Rank": "sparq-x_rank",
            "Speed Score": "speed_score",
            "Speed Score Rank": "speed_score_rank",
            "Throw Velocity": "throw_velocity",
            "Throw Velocity Rank": "throw_velocity_rank",
            "Vertical Jump": "vertical_jump",
            "Vertical Jump Rank": "vertical_jump_rank",
            "Wonderlic Score": "wonderlic_score",
            "Wonderlic Score Rank": "wonderlic_score_rank",
        }
        wm = {
            wm_mapping[k]: v
            for k, v in data["Workout Metrics"].items()
            if k in wm_mapping.keys()
        }
        context.update(wm)
        return wm

    def players(self, content):
        """
        Parses list of players, with ids, from playerprofiler

        Args:
            content(dict)

        Returns:
            list: of dict

        """
        try:
            data = json.loads(content)

        except Exception as e:
            data = None
            logging.exception("could not load content: {}".format(e))

        if data:
            return [
                {
                    "site": "playerprofiler",
                    "site_player_name": p.get("Full Name"),
                    "site_player_id": p.get("Player_ID"),
                }
                for p in data["data"]["Players"]
            ]
        else:
            return None

    def rankings(self, content):
        """
        Parses current season, dynasty, and weekly rankings from playerprofiler

        Args:
            content(dict)

        Returns:
            list: of dict

        """
        vals = []
        positions = ["QB", "RB", "WR", "TE"]
        rtypes = ["Dynasty", "Rookie", "Seasonal", "Weekly"]
        rankings = content["data"]
        for rt in rtypes:
            for pos in positions:
                vals.append(rankings[rt][pos])
        return vals


if __name__ == "__main__":
    pass
