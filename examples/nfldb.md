# Structure of the nfldb Database

## Table agg_play

Part of nfldb. Stores a row for each play aggregating statistics from the corresponding rows in the play_player table.

    CREATE TABLE public.agg_play
    (
      gsis_id gameid NOT NULL,
      drive_id usmallint NOT NULL,
      play_id usmallint NOT NULL,
      defense_ast smallint NOT NULL DEFAULT 0,
      defense_ffum smallint NOT NULL DEFAULT 0,
      defense_fgblk smallint NOT NULL DEFAULT 0,
      defense_frec smallint NOT NULL DEFAULT 0,
      defense_frec_tds smallint NOT NULL DEFAULT 0,
      defense_frec_yds smallint NOT NULL DEFAULT 0,
      defense_int smallint NOT NULL DEFAULT 0,
      defense_int_tds smallint NOT NULL DEFAULT 0,
      defense_int_yds smallint NOT NULL DEFAULT 0,
      defense_misc_tds smallint NOT NULL DEFAULT 0,
      defense_misc_yds smallint NOT NULL DEFAULT 0,
      defense_pass_def smallint NOT NULL DEFAULT 0,
      defense_puntblk smallint NOT NULL DEFAULT 0,
      defense_qbhit smallint NOT NULL DEFAULT 0,
      defense_safe smallint NOT NULL DEFAULT 0,
      defense_sk real NOT NULL DEFAULT 0.0,
      defense_sk_yds smallint NOT NULL DEFAULT 0,
      defense_tkl smallint NOT NULL DEFAULT 0,
      defense_tkl_loss smallint NOT NULL DEFAULT 0,
      defense_tkl_loss_yds smallint NOT NULL DEFAULT 0,
      defense_tkl_primary smallint NOT NULL DEFAULT 0,
      defense_xpblk smallint NOT NULL DEFAULT 0,
      fumbles_forced smallint NOT NULL DEFAULT 0,
      fumbles_lost smallint NOT NULL DEFAULT 0,
      fumbles_notforced smallint NOT NULL DEFAULT 0,
      fumbles_oob smallint NOT NULL DEFAULT 0,
      fumbles_rec smallint NOT NULL DEFAULT 0,
      fumbles_rec_tds smallint NOT NULL DEFAULT 0,
      fumbles_rec_yds smallint NOT NULL DEFAULT 0,
      fumbles_tot smallint NOT NULL DEFAULT 0,
      kicking_all_yds smallint NOT NULL DEFAULT 0,
      kicking_downed smallint NOT NULL DEFAULT 0,
      kicking_fga smallint NOT NULL DEFAULT 0,
      kicking_fgb smallint NOT NULL DEFAULT 0,
      kicking_fgm smallint NOT NULL DEFAULT 0,
      kicking_fgm_yds smallint NOT NULL DEFAULT 0,
      kicking_fgmissed smallint NOT NULL DEFAULT 0,
      kicking_fgmissed_yds smallint NOT NULL DEFAULT 0,
      kicking_i20 smallint NOT NULL DEFAULT 0,
      kicking_rec smallint NOT NULL DEFAULT 0,
      kicking_rec_tds smallint NOT NULL DEFAULT 0,
      kicking_tot smallint NOT NULL DEFAULT 0,
      kicking_touchback smallint NOT NULL DEFAULT 0,
      kicking_xpa smallint NOT NULL DEFAULT 0,
      kicking_xpb smallint NOT NULL DEFAULT 0,
      kicking_xpmade smallint NOT NULL DEFAULT 0,
      kicking_xpmissed smallint NOT NULL DEFAULT 0,
      kicking_yds smallint NOT NULL DEFAULT 0,
      kickret_fair smallint NOT NULL DEFAULT 0,
      kickret_oob smallint NOT NULL DEFAULT 0,
      kickret_ret smallint NOT NULL DEFAULT 0,
      kickret_tds smallint NOT NULL DEFAULT 0,
      kickret_touchback smallint NOT NULL DEFAULT 0,
      kickret_yds smallint NOT NULL DEFAULT 0,
      passing_att smallint NOT NULL DEFAULT 0,
      passing_cmp smallint NOT NULL DEFAULT 0,
      passing_cmp_air_yds smallint NOT NULL DEFAULT 0,
      passing_incmp smallint NOT NULL DEFAULT 0,
      passing_incmp_air_yds smallint NOT NULL DEFAULT 0,
      passing_int smallint NOT NULL DEFAULT 0,
      passing_sk smallint NOT NULL DEFAULT 0,
      passing_sk_yds smallint NOT NULL DEFAULT 0,
      passing_tds smallint NOT NULL DEFAULT 0,
      passing_twopta smallint NOT NULL DEFAULT 0,
      passing_twoptm smallint NOT NULL DEFAULT 0,
      passing_twoptmissed smallint NOT NULL DEFAULT 0,
      passing_yds smallint NOT NULL DEFAULT 0,
      punting_blk smallint NOT NULL DEFAULT 0,
      punting_i20 smallint NOT NULL DEFAULT 0,
      punting_tot smallint NOT NULL DEFAULT 0,
      punting_touchback smallint NOT NULL DEFAULT 0,
      punting_yds smallint NOT NULL DEFAULT 0,
      puntret_downed smallint NOT NULL DEFAULT 0,
      puntret_fair smallint NOT NULL DEFAULT 0,
      puntret_oob smallint NOT NULL DEFAULT 0,
      puntret_tds smallint NOT NULL DEFAULT 0,
      puntret_tot smallint NOT NULL DEFAULT 0,
      puntret_touchback smallint NOT NULL DEFAULT 0,
      puntret_yds smallint NOT NULL DEFAULT 0,
      receiving_rec smallint NOT NULL DEFAULT 0,
      receiving_tar smallint NOT NULL DEFAULT 0,
      receiving_tds smallint NOT NULL DEFAULT 0,
      receiving_twopta smallint NOT NULL DEFAULT 0,
      receiving_twoptm smallint NOT NULL DEFAULT 0,
      receiving_twoptmissed smallint NOT NULL DEFAULT 0,
      receiving_yac_yds smallint NOT NULL DEFAULT 0,
      receiving_yds smallint NOT NULL DEFAULT 0,
      rushing_att smallint NOT NULL DEFAULT 0,
      rushing_loss smallint NOT NULL DEFAULT 0,
      rushing_loss_yds smallint NOT NULL DEFAULT 0,
      rushing_tds smallint NOT NULL DEFAULT 0,
      rushing_twopta smallint NOT NULL DEFAULT 0,
      rushing_twoptm smallint NOT NULL DEFAULT 0,
      rushing_twoptmissed smallint NOT NULL DEFAULT 0,
      rushing_yds smallint NOT NULL DEFAULT 0
    )
    
## Table drive

Part of nfldb. Stores a row for each drive in a single game.


    CREATE TABLE public.drive
    (
      gsis_id gameid NOT NULL,
      drive_id usmallint NOT NULL,
      start_field field_pos,
      start_time game_time NOT NULL,
      end_field field_pos,
      end_time game_time NOT NULL,
      pos_team character varying(3) NOT NULL,
      pos_time pos_period,
      first_downs usmallint NOT NULL,
      result text,
      penalty_yards smallint NOT NULL,
      yards_gained smallint NOT NULL,
      play_count usmallint NOT NULL,
      time_inserted utctime NOT NULL,
      time_updated utctime NOT NULL
    )
    
## Table dst

Created by EWT. Stores a row for defense/special teams for each week played in fantasy season.

    CREATE TABLE public.dst
    (
      dst_id integer NOT NULL DEFAULT nextval('dst_dst_id_seq'::regclass),
      season_year smallint,
      week smallint,
      team_id smallint,
      team_code character varying,
      opp character varying,
      gsis_id character varying,
      fantasy_points smallint,
      pts_allowed smallint,
      sacks smallint,
      qb_hits smallint,
      tfl smallint,
      def_td smallint,
      return_td smallint,
      "int" smallint,
      fum_rec smallint,
      safeties smallint
    )
    
## Table fl_models

Created by EWT. Stores fantasylabs models json in model column, one per week per modelname.

    CREATE TABLE public.fl_models
    (
      fl_models_id integer NOT NULL DEFAULT nextval('fl_models_fl_models_id_seq'::regclass),
      ts timestamp with time zone DEFAULT now(),
      modelname character varying(25),
      modeldate character varying(10),
      season_year smallint,
      week smallint,
      model jsonb
    )
    
## Table fo_dl

Created by EWT. FootballOutsiders defensive line stats.
This table is highly incomplete - only has a 3 weeks from 2016 season 

    CREATE TABLE public.fo_dl
    (
      fo_dl_id integer NOT NULL DEFAULT nextval('fo_dl_fo_dl_id_seq'::regclass),
      season_year smallint NOT NULL,
      week smallint NOT NULL,
      team character varying(10) NOT NULL,
      pass_rank smallint NOT NULL,
      sacks smallint,
      adj_sack_rate numeric NOT NULL,
      rush_rank smallint NOT NULL,
      adj_line_yards numeric NOT NULL,
      stuffed numeric NOT NULL,
      stuffed_rank smallint NOT NULL,
      open_field_yards numeric NOT NULL,
      open_field_rank smallint NOT NULL,
      rb_yards numeric NOT NULL,
      sec_level_yards numeric NOT NULL,
      sec_level_rank smallint NOT NULL,
      power_success numeric NOT NULL,
      power_rank smallint NOT NULL
    )

## Table game

Part of nfldb. Stores a row for each NFL game in the preseason, regular season and postseason dating back to 2009. 
This includes games that are scheduled in the future but have not been played.

    CREATE TABLE public.game
    (
      gsis_id gameid NOT NULL,
      gamekey character varying(5),
      start_time utctime NOT NULL,
      week usmallint NOT NULL,
      day_of_week game_day NOT NULL,
      season_year usmallint NOT NULL,
      season_type season_phase NOT NULL,
      finished boolean NOT NULL,
      home_team character varying(3) NOT NULL,
      home_score usmallint NOT NULL,
      home_score_q1 usmallint,
      home_score_q2 usmallint,
      home_score_q3 usmallint,
      home_score_q4 usmallint,
      home_score_q5 usmallint,
      home_turnovers usmallint NOT NULL,
      away_team character varying(3) NOT NULL,
      away_score usmallint NOT NULL,
      away_score_q1 usmallint,
      away_score_q2 usmallint,
      away_score_q3 usmallint,
      away_score_q4 usmallint,
      away_score_q5 usmallint,
      away_turnovers usmallint NOT NULL,
      time_inserted utctime NOT NULL,
      time_updated utctime NOT NULL
    )

## Table gamesmeta

Created by EWT. Has scores + odds. Useful for joining w/ ML datasets.


    CREATE TABLE public.gamesmeta
    (
      games_meta_id integer NOT NULL DEFAULT nextval('gamesmeta_games_meta_id_seq'::regclass),
      gsis_id gameid,
      season_year smallint,
      week smallint,
      game_date date NOT NULL,
      team_code character varying NOT NULL,
      opp character varying NOT NULL,
      days_last_game smallint,
      q1 smallint,
      q2 smallint,
      q3 smallint,
      q4 smallint,
      ot1 smallint,
      s smallint,
      is_ot boolean,
      opening_spread numeric,
      opening_game_ou numeric,
      opening_implied_total numeric,
      consensus_spread numeric,
      consensus_game_ou numeric,
      consensus_implied_total numeric,
      is_home boolean
    )
    
## Table meta

Created by nfldb. Stores information about the database or about the state of the world. 
For example, it keeps track of the version of the database and the current week of the current NFL season.

    CREATE TABLE public.meta
    (
      version smallint,
      last_roster_download utctime NOT NULL,
      season_type season_phase,
      season_year usmallint,
      week usmallint
    )
    
## Table odds

Created by EWT. Stores odds scraped (I think) from footballlocks.com

    CREATE TABLE public.odds
    (
      odds_id integer NOT NULL DEFAULT nextval('odds_odds_id_seq'::regclass),
      gsis_id gameid,
      season_year smallint,
      week smallint,
      dt character varying(50),
      away_team character varying(5),
      home_team character varying(5),
      spread numeric,
      game_total numeric,
      away_implied numeric,
      home_implied numeric,
      money_odds character varying(50)
    )
    
## Table play

Created by nfldb. Stores a row for each play in a single drive.

    CREATE TABLE public.play
    (
      gsis_id gameid NOT NULL,
      drive_id usmallint NOT NULL,
      play_id usmallint NOT NULL,
      "time" game_time NOT NULL,
      pos_team character varying(3) NOT NULL,
      yardline field_pos,
      down smallint,
      yards_to_go smallint,
      description text,
      note text,
      time_inserted utctime NOT NULL,
      time_updated utctime NOT NULL,
      first_down smallint NOT NULL DEFAULT 0,
      fourth_down_att smallint NOT NULL DEFAULT 0,
      fourth_down_conv smallint NOT NULL DEFAULT 0,
      fourth_down_failed smallint NOT NULL DEFAULT 0,
      passing_first_down smallint NOT NULL DEFAULT 0,
      penalty smallint NOT NULL DEFAULT 0,
      penalty_first_down smallint NOT NULL DEFAULT 0,
      penalty_yds smallint NOT NULL DEFAULT 0,
      rushing_first_down smallint NOT NULL DEFAULT 0,
      third_down_att smallint NOT NULL DEFAULT 0,
      third_down_conv smallint NOT NULL DEFAULT 0,
      third_down_failed smallint NOT NULL DEFAULT 0,
      timeout smallint NOT NULL DEFAULT 0,
      xp_aborted smallint NOT NULL DEFAULT 0
    )
    
## Table play_player

Created by nfldb. Stores a row for each player statistic in a single play.

    CREATE TABLE public.play_player
    (
      gsis_id gameid NOT NULL,
      drive_id usmallint NOT NULL,
      play_id usmallint NOT NULL,
      player_id character varying(10) NOT NULL,
      team character varying(3) NOT NULL,
      defense_ast smallint NOT NULL DEFAULT 0,
      defense_ffum smallint NOT NULL DEFAULT 0,
      defense_fgblk smallint NOT NULL DEFAULT 0,
      defense_frec smallint NOT NULL DEFAULT 0,
      defense_frec_tds smallint NOT NULL DEFAULT 0,
      defense_frec_yds smallint NOT NULL DEFAULT 0,
      defense_int smallint NOT NULL DEFAULT 0,
      defense_int_tds smallint NOT NULL DEFAULT 0,
      defense_int_yds smallint NOT NULL DEFAULT 0,
      defense_misc_tds smallint NOT NULL DEFAULT 0,
      defense_misc_yds smallint NOT NULL DEFAULT 0,
      defense_pass_def smallint NOT NULL DEFAULT 0,
      defense_puntblk smallint NOT NULL DEFAULT 0,
      defense_qbhit smallint NOT NULL DEFAULT 0,
      defense_safe smallint NOT NULL DEFAULT 0,
      defense_sk real NOT NULL DEFAULT 0.0,
      defense_sk_yds smallint NOT NULL DEFAULT 0,
      defense_tkl smallint NOT NULL DEFAULT 0,
      defense_tkl_loss smallint NOT NULL DEFAULT 0,
      defense_tkl_loss_yds smallint NOT NULL DEFAULT 0,
      defense_tkl_primary smallint NOT NULL DEFAULT 0,
      defense_xpblk smallint NOT NULL DEFAULT 0,
      fumbles_forced smallint NOT NULL DEFAULT 0,
      fumbles_lost smallint NOT NULL DEFAULT 0,
      fumbles_notforced smallint NOT NULL DEFAULT 0,
      fumbles_oob smallint NOT NULL DEFAULT 0,
      fumbles_rec smallint NOT NULL DEFAULT 0,
      fumbles_rec_tds smallint NOT NULL DEFAULT 0,
      fumbles_rec_yds smallint NOT NULL DEFAULT 0,
      fumbles_tot smallint NOT NULL DEFAULT 0,
      kicking_all_yds smallint NOT NULL DEFAULT 0,
      kicking_downed smallint NOT NULL DEFAULT 0,
      kicking_fga smallint NOT NULL DEFAULT 0,
      kicking_fgb smallint NOT NULL DEFAULT 0,
      kicking_fgm smallint NOT NULL DEFAULT 0,
      kicking_fgm_yds smallint NOT NULL DEFAULT 0,
      kicking_fgmissed smallint NOT NULL DEFAULT 0,
      kicking_fgmissed_yds smallint NOT NULL DEFAULT 0,
      kicking_i20 smallint NOT NULL DEFAULT 0,
      kicking_rec smallint NOT NULL DEFAULT 0,
      kicking_rec_tds smallint NOT NULL DEFAULT 0,
      kicking_tot smallint NOT NULL DEFAULT 0,
      kicking_touchback smallint NOT NULL DEFAULT 0,
      kicking_xpa smallint NOT NULL DEFAULT 0,
      kicking_xpb smallint NOT NULL DEFAULT 0,
      kicking_xpmade smallint NOT NULL DEFAULT 0,
      kicking_xpmissed smallint NOT NULL DEFAULT 0,
      kicking_yds smallint NOT NULL DEFAULT 0,
      kickret_fair smallint NOT NULL DEFAULT 0,
      kickret_oob smallint NOT NULL DEFAULT 0,
      kickret_ret smallint NOT NULL DEFAULT 0,
      kickret_tds smallint NOT NULL DEFAULT 0,
      kickret_touchback smallint NOT NULL DEFAULT 0,
      kickret_yds smallint NOT NULL DEFAULT 0,
      passing_att smallint NOT NULL DEFAULT 0,
      passing_cmp smallint NOT NULL DEFAULT 0,
      passing_cmp_air_yds smallint NOT NULL DEFAULT 0,
      passing_incmp smallint NOT NULL DEFAULT 0,
      passing_incmp_air_yds smallint NOT NULL DEFAULT 0,
      passing_int smallint NOT NULL DEFAULT 0,
      passing_sk smallint NOT NULL DEFAULT 0,
      passing_sk_yds smallint NOT NULL DEFAULT 0,
      passing_tds smallint NOT NULL DEFAULT 0,
      passing_twopta smallint NOT NULL DEFAULT 0,
      passing_twoptm smallint NOT NULL DEFAULT 0,
      passing_twoptmissed smallint NOT NULL DEFAULT 0,
      passing_yds smallint NOT NULL DEFAULT 0,
      punting_blk smallint NOT NULL DEFAULT 0,
      punting_i20 smallint NOT NULL DEFAULT 0,
      punting_tot smallint NOT NULL DEFAULT 0,
      punting_touchback smallint NOT NULL DEFAULT 0,
      punting_yds smallint NOT NULL DEFAULT 0,
      puntret_downed smallint NOT NULL DEFAULT 0,
      puntret_fair smallint NOT NULL DEFAULT 0,
      puntret_oob smallint NOT NULL DEFAULT 0,
      puntret_tds smallint NOT NULL DEFAULT 0,
      puntret_tot smallint NOT NULL DEFAULT 0,
      puntret_touchback smallint NOT NULL DEFAULT 0,
      puntret_yds smallint NOT NULL DEFAULT 0,
      receiving_rec smallint NOT NULL DEFAULT 0,
      receiving_tar smallint NOT NULL DEFAULT 0,
      receiving_tds smallint NOT NULL DEFAULT 0,
      receiving_twopta smallint NOT NULL DEFAULT 0,
      receiving_twoptm smallint NOT NULL DEFAULT 0,
      receiving_twoptmissed smallint NOT NULL DEFAULT 0,
      receiving_yac_yds smallint NOT NULL DEFAULT 0,
      receiving_yds smallint NOT NULL DEFAULT 0,
      rushing_att smallint NOT NULL DEFAULT 0,
      rushing_loss smallint NOT NULL DEFAULT 0,
      rushing_loss_yds smallint NOT NULL DEFAULT 0,
      rushing_tds smallint NOT NULL DEFAULT 0,
      rushing_twopta smallint NOT NULL DEFAULT 0,
      rushing_twoptm smallint NOT NULL DEFAULT 0,
      rushing_twoptmissed smallint NOT NULL DEFAULT 0,
      rushing_yds smallint NOT NULL DEFAULT 0
    )
    
## Table player

Created by nfldb. Stores stores ephemeral data about players. 
Namely, it is the most current information about each player known by nfldb.

    CREATE TABLE public.player
    (
      player_id character varying(10) NOT NULL,
      gsis_name character varying(75),
      full_name character varying(100),
      first_name character varying(100),
      last_name character varying(100),
      team character varying(3) NOT NULL,
      "position" player_pos NOT NULL,
      profile_id integer,
      profile_url character varying(255),
      uniform_number usmallint,
      birthdate character varying(75),
      college character varying(255),
      height usmallint,
      weight usmallint,
      years_pro usmallint,
      status player_status NOT NULL
    )
    
## Table salaries

Created by EWT. Stores a row for each player salary for each week.

    CREATE TABLE public.salaries
    (
      salaries_id integer NOT NULL DEFAULT nextval('salaries_salaries_id_seq'::regclass),
      season_year smallint NOT NULL,
      week smallint NOT NULL,
      player_id character varying(10),
      team character varying(10),
      source character varying(50) NOT NULL,
      source_player_id character varying(50) NOT NULL,
      source_player_name character varying(50) NOT NULL,
      dfs_site character varying(5) NOT NULL,
      dfs_position character varying(5) NOT NULL,
      salary smallint NOT NULL
    )
    
## Table snapcounts

Created by EWT. FootballOutsiders defensive line stats.
This table is highly incomplete - only has a weeks 1-13 from 2016 season 

    CREATE TABLE public.snapcounts
    (
      snapcounts_id integer NOT NULL DEFAULT nextval('snapcounts_snapcounts_id_seq'::regclass),
      player_id character varying(10) NOT NULL,
      gsis_id gameid,
      season smallint,
      week smallint,
      first_name character varying(50),
      last_name character varying(50),
      "position" character varying(5),
      team character varying(5),
      site character varying(50),
      site_player_id character varying(50),
      site_player_name character varying(50),
      site_player_position character varying(10),
      site_player_team character varying(10),
      started boolean,
      total_snaps smallint,
      def_snap_pct numeric,
      def_snaps smallint,
      off_snap_pct numeric,
      off_snaps smallint,
      st_snap_pct numeric,
      st_snaps smallint
    )
    
## Table team

Created by nfldb. Stores a row for each team in the league. 
There is also a row that corresponds to an unknown team called UNK. 
This is used for players that are not on any current roster.

    CREATE TABLE public.team
    (
      team_id character varying(3) NOT NULL,
      city character varying(50) NOT NULL,
      name character varying(50) NOT NULL,
    )
