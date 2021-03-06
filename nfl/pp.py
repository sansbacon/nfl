"""

# pp.py
# classes to scrape and parse plyr proflr dot com

"""

import logging

from namematcher.xref import Site
from sportscraper.scraper import RequestScraper


class Scraper(RequestScraper):
    """
    For use by subscribers

    """

    @property
    def base_url(self):
        return "https://www.playerprofiler.com/wp-admin/admin-ajax.php?"

    def depth_chart(self, site_team_id):
        """
        Gets one team's depth chart from playerprofiler

        Args:
            site_team_id(str):

        Returns:
            dict

        """
        headers = {
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/69.0.3497.100 Safari/537.36 OPR/56.0.3051.99",
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://www.playerprofiler.com/depth-charts/{site_team_id}/",
            "Connection": "keep-alive",
        }

        params = {"action": "playerprofiler_api", "endpoint": f"/team/{site_team_id}"}
        return self.get_json(self.base_url, headers=headers, params=params)

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

    @classmethod
    def depth_chart(cls, content):
        """

        Args:
            content(dict):

        Returns:
            dict, list of dict

        """
        player_positions = content["data"]["Players"]
        info = content["data"]["Info"]
        team_data = {
            "site_team_id": info["Team"],
            "run_pct": info["Run %"],
            "pass_pct": info["Pass %"],
            "two_wr": info["2 WRs"],
            "three_wr": info["3 WRs"],
            "shotgun": info["Shotgun"],
            "under_center": info["UnderCenter"],
        }
        player_data = []
        for position, players in player_positions.items():
            for player in players:
                player_dict = {
                    k.lower().replace(" ", "_"): v for k, v in player.items()
                }
                player_dict["source_player_position"] = position
                player_data.append(player_dict)
        return team_data, player_data

    @classmethod
    def player_college_performance(cls, data):
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

    @classmethod
    def player_core(self, content):
        """
        Takes player dict, returns core

        Args:
            player:

        Returns:
            dict

        """
        context = {}
        player_node = content["data"]["Player"]
        player = {
            "source": "playerprofiler",
            "source_player_id": player_node["Player_ID"],
        }
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
            for k, v in player_node["Core"].items()
            if k in core_mapping.keys()
        }
        context.update(core)

        ## Core has nested data as well
        try:
            context["source_team_name"] = player_node["Core"]["Team"]["Name"]
        except (ValueError, KeyError):
            pass
        try:
            context["source_team_id"] = player_node["Core"]["Team"]["Team_ID"]
        except (ValueError, KeyError):
            pass
        try:
            context["best_comparables"] = [
                v["Full Name"] for k, v in player_node["Core"].items() if "Best" in k
            ]
        except (ValueError, KeyError):
            pass
        return context

    @classmethod
    def player_game_logs(cls, data):
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

    @classmethod
    def player_medical_history(cls, data):
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

    @classmethod
    def player_performance_metrics(cls, data):
        """
        Takes player dict, returns performance metrics

        Args:
            data:

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

    @classmethod
    def player_workout_metrics(cls, data):
        """
        Takes player dict, returns workout metrics

        Args:
            data:

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

    @classmethod
    def players(cls, content):
        """
        Parses list of players, with ids, from playerprofiler

        Args:
            content(dict)

        Returns:
            list: of dict

        """
        return [
            {
                "source": "playerprofiler",
                "source_player_name": p.get("Full Name"),
                "source_player_id": p.get("Player_ID"),
                "source_player_position": p.get("Position"),
                "source_player_team": p.get("Team"),
            }
            for p in content["data"]["Players"]
        ]

    @classmethod
    def rankings(cls, content):
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
        rankings = content["data"]["rankings"]
        for rt in rtypes:
            for pos in positions:
                vals.append(rankings[rt][pos])
        return vals


class Agent:
    """
    Common pp tasks

    """

    def __init__(self, db=None):
        logging.getLogger(__name__).addHandler(logging.NullHandler())
        self._s = Scraper()
        self._p = Parser()
        self._x = Xref(db=db)

    def player_xref(self):
        """
        Matches players to table

        Returns:

        """
        # get site players
        # {'site': 'playerprofiler',
        #  'site_player_name': 'Cyrus Gray',
        #  'site_player_id': 'CG-2150'}
        site_players = Parser.players(self._s.players())
        return self._x.match_base(site_players)


class Xref(Site):
    """
    Used to cross-reference site players

    """

    def __init__(self, db):
        """

        Args:
            db(NFLPostgres): instance

        """
        super().__init__(db=db)
        self.source_name = "playerprofiler"


if __name__ == "__main__":
    pass
