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

## Table draft

Created by EWT. Stores a row for each draft pick in each season.

    CREATE TABLE public.draft
    (
      draft_id integer NOT NULL DEFAULT nextval('draft_draft_id_seq'::regclass),
      player_id character varying(10) NOT NULL,
      full_name character varying(100),
      team character varying(3) NOT NULL,
      draft_year smallint NOT NULL,
      draft_round smallint NOT NULL,
      draft_overall_pick smallint,
      source character varying(50) NOT NULL,
      source_player_id character varying NOT NULL,
      CONSTRAINT draft_pkey PRIMARY KEY (draft_id),
      CONSTRAINT player_team_fkey FOREIGN KEY (team)
          REFERENCES public.team (team_id) MATCH SIMPLE
          ON UPDATE CASCADE ON DELETE RESTRICT,
      CONSTRAINT player_player_id_check CHECK (char_length(player_id::text) = 10)
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

Created by EWT. Has scores + odds. Useful for joining w/ other datasets.


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

## Table player_xref

Created by EWT. Stores a row for each player from each source, such as ESPN or NFL.com.

    CREATE TABLE public.player_xref
    (
      player_xref_id integer NOT NULL DEFAULT nextval('player_xref_player_xref_id_seq'::regclass),
      nflcom_player_id character varying NOT NULL,
      source character varying(50) NOT NULL,
      source_player_id character varying(100) NOT NULL,
      source_player_name character varying(100) NOT NULL,
      source_player_team character varying(5),
      source_player_position character varying(10),
      CONSTRAINT player_xref_pkey PRIMARY KEY (player_xref_id),
      CONSTRAINT player_xref_nflcom_player_id_source_key UNIQUE (nflcom_player_id, source),
      CONSTRAINT player_xref_source_player_id_source_key UNIQUE (source_player_id, source)
    )

## Table salaries

Created by EWT. Stores a row for each player dfs result (from rg.com) for each week.

    CREATE TABLE public.rotoguru_dk
    (
      rotoguru_dk_id integer NOT NULL DEFAULT nextval('rotoguru_dk_rotoguru_dk_id_seq'::regclass),
      season_year smallint NOT NULL,
      week smallint NOT NULL,
      gid character varying,
      player_name character varying NOT NULL,
      player_pos character varying NOT NULL,
      team_code character varying NOT NULL,
      ha character varying NOT NULL,
      opp character varying NOT NULL,
      dk_points numeric NOT NULL,
      dk_salary smallint NOT NULL,
      gsis_id character varying,
      CONSTRAINT rotoguru_dk_pkey PRIMARY KEY (rotoguru_dk_id),
      CONSTRAINT rotoguru_dk_season_year_week_player_name_dk_points_key UNIQUE (season_year, week, player_name, dk_points)
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

## Table teamstats_offense_yearly

Created by EWT. Yearly team offsense stats. Courtesy of pro-football-reference.

    CREATE TABLE public.teamstats_offense_yearly
    (
      teamstats_offense_yearly_id integer NOT NULL DEFAULT nextval('teamstats_offense_yearly_teamstats_offense_yearly_id_seq'::regclass),
      season_year smallint NOT NULL,
      team character varying NOT NULL,
      pass_cmp smallint NOT NULL,
      pass_att smallint NOT NULL,
      pass_yds smallint NOT NULL,
      pass_int smallint NOT NULL,
      pass_td smallint NOT NULL,
      pass_sacked smallint NOT NULL,
      pass_sacked_yds smallint NOT NULL,
      exp_pts_pass numeric NOT NULL,
      rush_att smallint NOT NULL,
      rush_yds smallint NOT NULL,
      rush_td smallint NOT NULL,
      exp_pts_rush numeric NOT NULL,
      fumbles smallint NOT NULL,
      two_pt_md smallint NOT NULL,
      two_pt_att smallint NOT NULL,
      fga smallint NOT NULL,
      fgm smallint NOT NULL,
      drives smallint NOT NULL,
      play_count_tip smallint NOT NULL,
      score_pct numeric NOT NULL,
      turnover_pct numeric NOT NULL,
      start_avg numeric NOT NULL,
      time_avg numeric NOT NULL,
      points_avg numeric NOT NULL,
      CONSTRAINT teamstats_offense_yearly_pkey PRIMARY KEY (teamstats_offense_yearly_id)
    )

## Table weekly_dvoa

Created by EWT. FootballOutsiders DVOA stats.

    CREATE TABLE public.weekly_dvoa
    (
      weekly_dvoa_id integer NOT NULL DEFAULT nextval('weekly_dvoa_weekly_dvoa_id_seq'::regclass),
      season_year integer NOT NULL,
      week smallint NOT NULL,
      team_code character varying(5) NOT NULL,
      opponent character(3),
      wl character varying(8),
      w smallint,
      l smallint,
      total_dvoa numeric,
      total_dvoa_rank smallint,
      weighted_dvoa numeric,
      weighted_dvoa_rank smallint,
      off_dvoa numeric,
      off_dvoa_rank smallint,
      off_pass_dvoa numeric,
      off_rush_dvoa numeric,
      weighted_off_dvoa numeric,
      weighted_off_dvoa_rank smallint,
      def_dvoa numeric,
      def_dvoa_rank smallint,
      def_pass_dvoa numeric,
      def_rush_dvoa numeric,
      weighted_def_dvoa numeric,
      weighted_def_dvoa_rank smallint,
      st_dvoa numeric,
      st_dvoa_rank smallint,
      weighted_st_dvoa numeric,
      weighted_st_dvoa_rank smallint,
      CONSTRAINT weekly_dvoa_pkey PRIMARY KEY (weekly_dvoa_id),
      CONSTRAINT weekly_dvoa_season_week_team_key UNIQUE (season_year, week, team_code)
    )

# Views

## air_yards

Created by EWT. Has air yards and YAC on per-play basis.

    CREATE MATERIALIZED VIEW public.air_yards AS 
     WITH qb AS (
             SELECT play_player.gsis_id,
                play_player.drive_id,
                play_player.play_id,
                play_player.team,
                play_player.passing_cmp,
                play_player.passing_att,
                play_player.passing_yds,
                play_player.passing_incmp_air_yds AS air_yds,
                play_player.player_id AS qb
               FROM play_player
              WHERE play_player.passing_incmp_air_yds > 0 AND (play_player.gsis_id::text IN ( SELECT game.gsis_id
                       FROM game
                      WHERE game.season_type = 'Regular'::season_phase)) AND play_player.passing_att > 0 AND play_player.passing_cmp = 0
            ), rcvr AS (
             SELECT qb.gsis_id,
                qb.drive_id,
                qb.play_id,
                qb.team,
                qb.passing_cmp,
                qb.passing_att,
                qb.passing_yds,
                qb.air_yds,
                qb.qb,
                pp.receiver,
                pp.receiving_rec,
                pp.receiving_yds,
                pp.receiving_yac_yds
               FROM qb
                 LEFT JOIN ( SELECT play_player.gsis_id,
                        play_player.drive_id,
                        play_player.play_id,
                        play_player.player_id,
                        play_player.team,
                        play_player.passing_att,
                        play_player.receiving_rec,
                        play_player.receiving_yds,
                        play_player.receiving_yac_yds,
                        play_player.player_id AS receiver
                       FROM play_player
                      WHERE play_player.passing_att = 0) pp ON qb.gsis_id::text = pp.gsis_id::text AND qb.drive_id::smallint = pp.drive_id::smallint AND qb.play_id::smallint = pp.play_id::smallint AND qb.team::text = pp.team::text
            ), icay AS (
             SELECT rcvr.receiver AS player_id,
                p2.full_name,
                rcvr.gsis_id,
                rcvr.drive_id,
                rcvr.play_id,
                rcvr.team,
                rcvr.receiving_rec,
                rcvr.air_yds,
                rcvr.receiving_yds,
                rcvr.receiving_yac_yds
               FROM rcvr
                 LEFT JOIN player p ON rcvr.qb::text = p.player_id::text
                 LEFT JOIN player p2 ON rcvr.receiver::text = p2.player_id::text
            ), cay AS (
             SELECT pp.player_id,
                p.full_name,
                pp.gsis_id,
                pp.drive_id,
                pp.play_id,
                pp.team,
                pp.receiving_rec,
                pp.receiving_yds - pp.receiving_yac_yds AS air_yds,
                pp.receiving_yds,
                pp.receiving_yac_yds
               FROM play_player pp
                 LEFT JOIN player p ON pp.player_id::text = p.player_id::text
              WHERE pp.receiving_rec = 1 AND (pp.gsis_id::text IN ( SELECT game.gsis_id
                       FROM game
                      WHERE game.season_type = 'Regular'::season_phase))
            ), comb AS (
             SELECT cay.player_id,
                cay.full_name,
                cay.gsis_id,
                cay.drive_id,
                cay.play_id,
                cay.team,
                cay.receiving_rec,
                cay.air_yds,
                cay.receiving_yds,
                cay.receiving_yac_yds
               FROM cay
            UNION ALL
             SELECT icay.player_id,
                icay.full_name,
                icay.gsis_id,
                icay.drive_id,
                icay.play_id,
                icay.team,
                icay.receiving_rec,
                icay.air_yds,
                icay.receiving_yds,
                icay.receiving_yac_yds
               FROM icay
            )
     SELECT g.season_year,
        comb.player_id,
        comb.full_name,
        comb.gsis_id,
        comb.drive_id,
        comb.play_id,
        comb.team,
        comb.receiving_rec,
        comb.air_yds,
        comb.receiving_yds,
        comb.receiving_yac_yds
       FROM comb
         JOIN game g ON comb.gsis_id::text = g.gsis_id::text
    WITH DATA;

## air_yards_summary

Created by EWT. Has air yards on per-season basis.

    CREATE OR REPLACE VIEW public.air_yards_summary AS 
     WITH ay AS (
             SELECT air_yards.season_year,
                air_yards.player_id,
                air_yards.team,
                count(air_yards.*) AS targ,
                round(avg(air_yards.air_yds), 1) AS aypt,
                sum(air_yards.air_yds) AS tot_ay
               FROM air_yards
              GROUP BY air_yards.season_year, air_yards.player_id, air_yards.team
            )
     SELECT ay.season_year,
        p.full_name,
        ay.team,
        p."position",
        ay.targ,
        ay.aypt,
        ay.tot_ay
       FROM ay
         LEFT JOIN player p ON ay.player_id::text = p.player_id::text
      WHERE ay.targ > 10
      ORDER BY ay.season_year DESC, ay.aypt DESC;

## cs_passing

Created by EWT. Selects QB stats from current season (fantasy & DFS) 

    CREATE VIEW cs_passing AS
    SELECT * from passing
    WHERE season_year = (SELECT MAX(season_year) FROM passing)

## cs_receiving

Created by EWT. Selects receiving stats from current season (fantasy & DFS) 

    CREATE VIEW cs_receiving AS
    SELECT * from receiving
    WHERE season_year = (SELECT MAX(season_year) FROM receiving)

## cs_rushing

Created by EWT. Selects rushing stats from current season (fantasy & DFS) 

    CREATE VIEW cs_rushing AS
    SELECT * from rushing
    WHERE season_year = (SELECT MAX(season_year) FROM rushing)

## cs_receiving_dvp

Created by EWT. Selects defense vs. position for receivers.

    CREATE OR REPLACE VIEW public.cs_receiving_dvp AS 
     SELECT cs_receiving.opp,
        cs_receiving."position",
        round(sum(cs_receiving.receiving_tar) / 13::numeric, 2) AS avg_tgt,
        round(sum(cs_receiving.receiving_yds) / 13::numeric, 2) AS avg_yds,
        round(sum(cs_receiving.receiving_tds) / 13::numeric, 2) AS avg_tds,
        round(sum(cs_receiving.fpts_dk) / 13::numeric, 2) AS avg_dk
       FROM cs_receiving
      GROUP BY cs_receiving.opp, cs_receiving."position"
      ORDER BY cs_receiving."position", (round(sum(cs_receiving.fpts_dk) / 13::numeric, 2)) DESC;

## cs_receiving_dvp

Created by EWT. Selects weekly snap counts.

    CREATE MATERIALIZED VIEW public.cs_snaps AS 
     WITH snaps AS (
             SELECT cws.week,
                cws.full_name,
                cws."position",
                cws.fpts_dk,
                cws.team,
                tg.opp,
                sc.off_snaps,
                sc.off_snap_pct,
                lag(sc.off_snaps, 1) OVER (ORDER BY cws.player_id, cws.team, cws.week) AS off_snaps_1bef,
                lag(sc.off_snaps, 2) OVER (ORDER BY cws.player_id, cws.team, cws.week) AS off_snaps_2bef,
                lag(sc.off_snaps, 3) OVER (ORDER BY cws.player_id, cws.team, cws.week) AS off_snaps_3bef
               FROM cs_weekly_stats cws
                 LEFT JOIN snapcounts sc ON cws.gsis_id::text = sc.gsis_id::text AND cws.player_id::text = sc.player_id::text
                 LEFT JOIN cs_teamgames tg ON cws.gsis_id::text = tg.gsis_id::text AND cws.team::text = tg.team::text
            )
     SELECT snaps.week,
        snaps.full_name,
        snaps."position",
        snaps.fpts_dk,
        snaps.team,
        snaps.opp,
        snaps.off_snaps,
        snaps.off_snap_pct,
        snaps.off_snaps_1bef,
        snaps.off_snaps_2bef,
        snaps.off_snaps_3bef,
        snaps.off_snaps - snaps.off_snaps_1bef AS d_snaps,
        snaps.off_snaps::numeric - round(((snaps.off_snaps_1bef + snaps.off_snaps_2bef + snaps.off_snaps_3bef) / 3)::numeric, 0) AS d2_snaps
       FROM snaps
      WHERE snaps."position" = 'WR'::player_pos
      ORDER BY snaps.week DESC, snaps.team, snaps.off_snaps DESC
    WITH DATA;

## cs_teamgames

Created by EWT. Selects all teamgames for current season.

    CREATE MATERIALIZED VIEW public.cs_teamgames AS 
     SELECT *
       FROM teamgames
      WHERE season_year = (SELECT max(season_year) FROM game)

## cs_weekly_stats

Created by EWT. Selects all player stats on per-week basis for this season.

    CREATE VIEW cs_weekly_stats AS
    SELECT * FROM weekly_stats
    WHERE season_year = (SELECT max(season_year) FROM weekly_stats)

## dk_points

Created by EWT. Merges player DK stats w/ DST.

    CREATE MATERIALIZED VIEW public.dkpts AS 
     SELECT ws.season_year,
        ws.week,
        ws.gsis_id,
        ws.player_id,
        ws.full_name,
        ws.team,
        ws.opp,
        ws."position" AS pos,
        ws.fpts_dk
       FROM weekly_stats ws
    UNION ALL
     SELECT dst.season_year,
        dst.week,
        dst.gsis_id,
        NULL::character varying AS player_id,
        dst.team_code::text || ' Defense'::text AS full_name,
        dst.team_code AS team,
        dst.opp,
        'DST'::player_pos AS pos,
        dst.fantasy_points AS fpts_dk
       FROM dst
      WHERE dst.season_year > 2008

## game_agg

Created by EWT. Aggregates game-level stats from play_player.

    CREATE MATERIALIZED VIEW public.game_agg AS 
     SELECT play_player.gsis_id,
        play_player.player_id,
        play_player.team,
        sum(play_player.passing_cmp) AS passing_cmp,
        sum(play_player.passing_att) AS passing_att,
        sum(play_player.passing_yds) AS passing_yds,
        sum(play_player.passing_int) AS passing_int,
        sum(play_player.passing_tds) AS passing_tds,
        sum(play_player.passing_twoptm) AS passing_twoptm,
        sum(play_player.rushing_att) AS rushing_att,
        sum(play_player.rushing_yds) AS rushing_yds,
        sum(play_player.rushing_tds) AS rushing_tds,
        sum(play_player.rushing_twoptm) AS rushing_twoptm,
        sum(play_player.receiving_tar) AS receiving_tar,
        sum(play_player.receiving_rec) AS receiving_rec,
        sum(play_player.receiving_yds) AS receiving_yds,
        sum(play_player.receiving_tds) AS receiving_tds,
        sum(play_player.receiving_twoptm) AS receiving_twoptm,
        sum(play_player.fumbles_lost) AS fumbles_lost,
        sum(play_player.fumbles_rec_tds) AS fumbles_rec_tds,
        sum(play_player.puntret_tds) AS puntret_tds,
        sum(play_player.kickret_tds) AS kickret_tds
       FROM play_player
      WHERE (play_player.gsis_id::text IN ( SELECT game.gsis_id
               FROM game
              WHERE game.season_type = 'Regular'::season_phase))
      GROUP BY play_player.gsis_id, play_player.player_id, play_player.team
    WITH DATA;

## incomplete_air_yards

Created by EWT. Incomplete air yards on a per-play basis.

    CREATE OR REPLACE VIEW public.incomplete_air_yards AS 
     WITH qb AS (
             SELECT play_player.gsis_id,
                play_player.drive_id,
                play_player.play_id,
                play_player.team,
                play_player.passing_cmp,
                play_player.passing_att,
                play_player.passing_yds,
                play_player.passing_incmp_air_yds AS incomplete_air_yds,
                play_player.player_id AS qb
               FROM play_player
              WHERE play_player.passing_incmp_air_yds > 0 AND (play_player.gsis_id::text IN ( SELECT game.gsis_id
                       FROM game
                      WHERE game.season_type = 'Regular'::season_phase)) AND play_player.passing_att > 0 AND play_player.passing_cmp = 0
            ), rcvr AS (
             SELECT qb.gsis_id,
                qb.drive_id,
                qb.play_id,
                qb.team,
                qb.passing_cmp,
                qb.passing_att,
                qb.passing_yds,
                qb.incomplete_air_yds,
                qb.qb,
                pp.receiver
               FROM qb
                 LEFT JOIN ( SELECT play_player.gsis_id,
                        play_player.drive_id,
                        play_player.play_id,
                        play_player.player_id,
                        play_player.team,
                        play_player.passing_att,
                        play_player.player_id AS receiver
                       FROM play_player
                      WHERE play_player.passing_att = 0) pp ON qb.gsis_id::text = pp.gsis_id::text AND qb.drive_id::smallint = pp.drive_id::smallint AND qb.play_id::smallint = pp.play_id::smallint AND qb.team::text = pp.team::text
            )
     SELECT rcvr.gsis_id,
        rcvr.drive_id,
        rcvr.play_id,
        rcvr.team,
        rcvr.incomplete_air_yds,
        rcvr.qb,
        p.full_name AS qb_name,
        rcvr.receiver,
        p2.full_name AS receiver_name
       FROM rcvr
         LEFT JOIN player p ON rcvr.qb::text = p.player_id::text
         LEFT JOIN player p2 ON rcvr.receiver::text = p2.player_id::text;

## offense_tds

Created by EWT. Every touchdown scored on offense since 2009.

    CREATE OR REPLACE VIEW public.offense_tds AS 
     WITH td AS (
             SELECT play.gsis_id,
                play.drive_id,
                play.play_id,
                (play."time").phase AS phase,
                play.yardline,
                play.down,
                play.yards_to_go
               FROM play
              WHERE play.note = 'TD'::text
            )
     SELECT g.season_year,
        g.week,
        g.gsis_id,
        d.pos_team AS team,
            CASE
                WHEN d.pos_team::text = g.home_team::text THEN g.away_team
                ELSE g.home_team
            END AS opp,
        td.drive_id,
        td.play_id,
        td.phase,
        ap.passing_yds,
        ap.passing_tds,
        ap.rushing_yds,
        ap.rushing_tds
       FROM td
         LEFT JOIN agg_play ap ON td.gsis_id::text = ap.gsis_id::text AND td.drive_id::smallint = ap.drive_id::smallint AND td.play_id::smallint = ap.play_id::smallint
         LEFT JOIN drive d ON td.gsis_id::text = d.gsis_id::text AND td.drive_id::smallint = d.drive_id::smallint
         LEFT JOIN game g ON td.gsis_id::text = g.gsis_id::text
      WHERE g.season_type = 'Regular'::season_phase AND (ap.passing_tds + ap.rushing_tds) > 0
      ORDER BY g.gsis_id;

## passing

Created by EWT. Weekly totals of player passing stats.

CREATE MATERIALIZED VIEW public.passing AS 
 WITH sq AS (
         SELECT weekly_stats.gsis_id,
            weekly_stats.season_year,
            weekly_stats.week,
            weekly_stats.player_id,
            weekly_stats.full_name,
            weekly_stats."position",
            weekly_stats.team,
            weekly_stats.opp,
            weekly_stats.passing_cmp,
            weekly_stats.passing_att,
            weekly_stats.passing_yds,
            weekly_stats.passing_int,
            weekly_stats.passing_tds,
            weekly_stats.passing_twoptm,
            weekly_stats.rushing_att,
            weekly_stats.rushing_yds,
            weekly_stats.rushing_tds,
            ntile(4) OVER (PARTITION BY weekly_stats.player_id, weekly_stats.season_year ORDER BY weekly_stats.passing_yds) AS pyards_bucket,
            weekly_stats.fpts_dk,
            ntile(4) OVER (PARTITION BY weekly_stats.player_id, weekly_stats.season_year ORDER BY weekly_stats.fpts_dk) AS dk_bucket
           FROM weekly_stats
          WHERE weekly_stats."position" = 'QB'::player_pos
        ), pyard25 AS (
         SELECT sq_1.player_id,
            sq_1.season_year,
            max(sq_1.passing_yds) AS pct25
           FROM sq sq_1
          WHERE sq_1.pyards_bucket = 1
          GROUP BY sq_1.player_id, sq_1.season_year
        ), pyard75 AS (
         SELECT sq_1.player_id,
            sq_1.season_year,
            max(sq_1.passing_yds) AS pct75
           FROM sq sq_1
          WHERE sq_1.pyards_bucket = 3
          GROUP BY sq_1.player_id, sq_1.season_year
        ), dk25 AS (
         SELECT sq_1.player_id,
            sq_1.season_year,
            max(sq_1.fpts_dk) AS pct25
           FROM sq sq_1
          WHERE sq_1.dk_bucket = 1
          GROUP BY sq_1.player_id, sq_1.season_year
        ), dk75 AS (
         SELECT sq_1.player_id,
            sq_1.season_year,
            max(sq_1.fpts_dk) AS pct75
           FROM sq sq_1
          WHERE sq_1.dk_bucket = 3
          GROUP BY sq_1.player_id, sq_1.season_year
        )
 SELECT sq.gsis_id,
    sq.season_year,
    sq.week,
    sq.player_id,
    sq.full_name,
    sq."position",
    sq.team,
    sq.opp,
    sq.passing_yds,
    sq.passing_tds,
    pyard25.pct25 AS pyard25,
    pyard75.pct75 AS pyard75,
    pyard75.pct75 - pyard25.pct25 AS pyards_iqr,
    sq.rushing_att,
    sq.rushing_yds,
    sq.rushing_tds,
    sq.fpts_dk,
    dk25.pct25 AS dk25,
    dk75.pct75 AS dk75,
    dk75.pct75 - dk25.pct25 AS dk_iqr,
    sq.passing_yds::numeric * 0.04 + (4 * sq.passing_tds)::numeric + (2 * sq.passing_twoptm)::numeric - sq.passing_int::numeric AS dk_pass_pts,
    sq.rushing_yds::numeric * 0.1 + (6 * sq.rushing_tds)::numeric AS dk_rush_pts
   FROM sq
     LEFT JOIN pyard25 ON sq.player_id::text = pyard25.player_id::text AND sq.season_year::smallint = pyard25.season_year::smallint
     LEFT JOIN pyard75 ON sq.player_id::text = pyard75.player_id::text AND sq.season_year::smallint = pyard75.season_year::smallint
     LEFT JOIN dk25 ON sq.player_id::text = dk25.player_id::text AND sq.season_year::smallint = dk25.season_year::smallint
     LEFT JOIN dk75 ON sq.player_id::text = dk75.player_id::text AND sq.season_year::smallint = dk75.season_year::smallint
  ORDER BY sq.player_id, sq.season_year, sq.week
WITH DATA;

## qb_i_air_yards

Created by EWT. Calcluates QB incomplete air yards on per-game basis.

    CREATE OR REPLACE VIEW public.qb_i_air_yards AS 
     WITH iay AS (
             SELECT play_player.gsis_id,
                play_player.player_id,
                play_player.team,
                sum(play_player.passing_cmp) AS passing_cmp,
                sum(play_player.passing_att) AS passing_att,
                sum(play_player.passing_yds) AS passing_yds,
                sum(play_player.passing_incmp_air_yds) AS incomplete_air_yds
               FROM play_player
              WHERE (play_player.gsis_id::text IN ( SELECT game.gsis_id
                       FROM game
                      WHERE game.season_type = 'Regular'::season_phase))
              GROUP BY play_player.gsis_id, play_player.player_id, play_player.team
            )
     SELECT iay.gsis_id,
        iay.player_id,
        iay.team,
        iay.passing_cmp,
        iay.passing_att,
        iay.passing_yds,
        iay.incomplete_air_yds
       FROM iay
      WHERE iay.passing_att > 0;

## receiving

Created by EWT. Selects receiving stats on per-week basis.

    CREATE MATERIALIZED VIEW public.receiving AS 
     WITH sq AS (
             SELECT weekly_stats.gsis_id,
                weekly_stats.season_year,
                weekly_stats.week,
                weekly_stats.player_id,
                weekly_stats.full_name,
                weekly_stats."position",
                weekly_stats.team,
                weekly_stats.opp,
                weekly_stats.receiving_tar,
                ntile(4) OVER (PARTITION BY weekly_stats.player_id, weekly_stats.season_year ORDER BY weekly_stats.receiving_tar) AS tar_bucket,
                weekly_stats.receiving_rec,
                weekly_stats.receiving_yds,
                weekly_stats.receiving_tds,
                weekly_stats.fpts_dk,
                ntile(4) OVER (PARTITION BY weekly_stats.player_id, weekly_stats.season_year ORDER BY weekly_stats.fpts_dk) AS dk_bucket
               FROM weekly_stats
              WHERE weekly_stats."position" = ANY (ARRAY['RB'::player_pos, 'WR'::player_pos, 'TE'::player_pos])
            ), tarp25 AS (
             SELECT sq_1.player_id,
                sq_1.season_year,
                max(sq_1.receiving_tar) AS pct25
               FROM sq sq_1
              WHERE sq_1.tar_bucket = 1
              GROUP BY sq_1.player_id, sq_1.season_year
            ), tarp75 AS (
             SELECT sq_1.player_id,
                sq_1.season_year,
                round(stddev_pop(sq_1.receiving_tar), 2) AS tar_stdev,
                max(sq_1.receiving_tar) AS pct75
               FROM sq sq_1
              WHERE sq_1.tar_bucket = 3
              GROUP BY sq_1.player_id, sq_1.season_year
            ), dk25 AS (
             SELECT sq_1.player_id,
                sq_1.season_year,
                max(sq_1.fpts_dk) AS pct25
               FROM sq sq_1
              WHERE sq_1.dk_bucket = 1
              GROUP BY sq_1.player_id, sq_1.season_year
            ), dk75 AS (
             SELECT sq_1.player_id,
                sq_1.season_year,
                max(sq_1.fpts_dk) AS pct75,
                round(stddev_pop(sq_1.fpts_dk), 2) AS dk_stdev
               FROM sq sq_1
              WHERE sq_1.dk_bucket = 3
              GROUP BY sq_1.player_id, sq_1.season_year
            )
     SELECT sq.gsis_id,
        sq.season_year,
        sq.week,
        sq.player_id,
        sq.full_name,
        sq."position",
        sq.team,
        sq.opp,
        sq.receiving_tar,
        tarp75.tar_stdev,
        tarp25.pct25 AS tar25,
        tarp75.pct75 AS tar75,
        tarp75.pct75 - tarp25.pct25 AS tar_iqr,
        sq.receiving_rec,
        sq.receiving_yds,
        sq.receiving_tds,
        sq.fpts_dk,
        dk75.dk_stdev,
        dk25.pct25 AS dk25,
        dk75.pct75 AS dk75,
        dk75.pct75 - dk25.pct25 AS dk_iqr,
        sq.receiving_rec::numeric + 0.1 * sq.receiving_yds::numeric + (6 * sq.receiving_tds)::numeric AS dk_rec_pts
       FROM sq
         LEFT JOIN tarp25 ON sq.player_id::text = tarp25.player_id::text AND sq.season_year::smallint = tarp25.season_year::smallint
         LEFT JOIN tarp75 ON sq.player_id::text = tarp75.player_id::text AND sq.season_year::smallint = tarp75.season_year::smallint
         LEFT JOIN dk25 ON sq.player_id::text = dk25.player_id::text AND sq.season_year::smallint = dk25.season_year::smallint
         LEFT JOIN dk75 ON sq.player_id::text = dk75.player_id::text AND sq.season_year::smallint = dk75.season_year::smallint
      ORDER BY sq.player_id, sq.season_year, sq.week
    WITH DATA;


## rushing

Created by EWT. Selects rushing stats on per-week basis.

    CREATE MATERIALIZED VIEW public.rushing AS 
     WITH sq AS (
             SELECT weekly_stats.gsis_id,
                weekly_stats.season_year,
                weekly_stats.week,
                weekly_stats.player_id,
                weekly_stats.full_name,
                weekly_stats."position",
                weekly_stats.team,
                weekly_stats.opp,
                weekly_stats.rushing_att,
                weekly_stats.rushing_yds,
                weekly_stats.rushing_tds,
                weekly_stats.rushing_twoptm,
                ntile(4) OVER (PARTITION BY weekly_stats.player_id, weekly_stats.season_year ORDER BY weekly_stats.rushing_yds) AS ryards_bucket,
                weekly_stats.fpts_dk,
                ntile(4) OVER (PARTITION BY weekly_stats.player_id, weekly_stats.season_year ORDER BY weekly_stats.fpts_dk) AS dk_bucket
               FROM weekly_stats
              WHERE weekly_stats."position" = 'RB'::player_pos
            ), ryard25 AS (
             SELECT sq_1.player_id,
                sq_1.season_year,
                max(sq_1.rushing_yds) AS pct25
               FROM sq sq_1
              WHERE sq_1.ryards_bucket = 1
              GROUP BY sq_1.player_id, sq_1.season_year
            ), ryard75 AS (
             SELECT sq_1.player_id,
                sq_1.season_year,
                max(sq_1.rushing_yds) AS pct75
               FROM sq sq_1
              WHERE sq_1.ryards_bucket = 3
              GROUP BY sq_1.player_id, sq_1.season_year
            ), dk25 AS (
             SELECT sq_1.player_id,
                sq_1.season_year,
                max(sq_1.fpts_dk) AS pct25
               FROM sq sq_1
              WHERE sq_1.dk_bucket = 1
              GROUP BY sq_1.player_id, sq_1.season_year
            ), dk75 AS (
             SELECT sq_1.player_id,
                sq_1.season_year,
                max(sq_1.fpts_dk) AS pct75
               FROM sq sq_1
              WHERE sq_1.dk_bucket = 3
              GROUP BY sq_1.player_id, sq_1.season_year
            )
     SELECT sq.gsis_id,
        sq.season_year,
        sq.week,
        sq.player_id,
        sq.full_name,
        sq."position",
        sq.team,
        sq.opp,
        sq.rushing_att,
        sq.rushing_yds,
        sq.rushing_tds,
        ryard25.pct25 AS ryard25,
        ryard75.pct75 AS ryard75,
        ryard75.pct75 - ryard25.pct25 AS ryards_iqr,
        sq.fpts_dk,
        dk25.pct25 AS dk25,
        dk75.pct75 AS dk75,
        dk75.pct75 - dk25.pct25 AS dk_iqr,
        sq.rushing_yds::numeric * 0.1 + (6 * sq.rushing_tds)::numeric AS dk_rush_pts
       FROM sq
         LEFT JOIN ryard25 ON sq.player_id::text = ryard25.player_id::text AND sq.season_year::smallint = ryard25.season_year::smallint
         LEFT JOIN ryard75 ON sq.player_id::text = ryard75.player_id::text AND sq.season_year::smallint = ryard75.season_year::smallint
         LEFT JOIN dk25 ON sq.player_id::text = dk25.player_id::text AND sq.season_year::smallint = dk25.season_year::smallint
         LEFT JOIN dk75 ON sq.player_id::text = dk75.player_id::text AND sq.season_year::smallint = dk75.season_year::smallint
      ORDER BY sq.player_id, sq.season_year, sq.week
    WITH DATA;

## team_scoring

Created by EWT. Selects rushing and passing TD on per-week basis.

    CREATE MATERIALIZED VIEW public.team_scoring AS 
     WITH t1 AS (
             SELECT weekly_stats.season_year,
                weekly_stats.week,
                weekly_stats.team,
                sum(weekly_stats.passing_tds) AS passtd,
                sum(weekly_stats.rushing_tds) AS rushtd
               FROM weekly_stats
              GROUP BY weekly_stats.season_year, weekly_stats.week, weekly_stats.team
              ORDER BY weekly_stats.season_year DESC, weekly_stats.week, weekly_stats.team
            )
     SELECT t1.season_year,
        t1.week,
        t1.team,
        t1.passtd,
        t1.rushtd,
        avg(t1.passtd) OVER (PARTITION BY t1.season_year, t1.team ORDER BY t1.season_year, t1.team, t1.week ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING) AS passtd_ytd,
        avg(t1.rushtd) OVER (PARTITION BY t1.season_year, t1.team ORDER BY t1.season_year, t1.team, t1.week ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING) AS rushtd_ytd
       FROM t1
    WITH DATA;

## teamgames

Likely unecessary due to gamesmeta

## vw_dfs

Created by EWT. Selects dfs points on a per-week basis.

    CREATE OR REPLACE VIEW public.vw_dfs AS 
     SELECT rg.gsis_id,
        rg.season_year,
        rg.week,
        rg.player_name,
        rg.player_pos,
        rg.team_code,
        rg.opp,
        rg.dk_salary,
        rg.dk_points,
        gm.is_home,
        gm.is_win,
        gm.consensus_game_ou AS ou,
        gm.consensus_implied_total AS imptot,
        gm.consensus_game_ou - gm.consensus_implied_total AS opp_imptot
       FROM rotoguru_dk rg
         LEFT JOIN gamesmeta gm ON rg.gsis_id::text = gm.gsis_id::text AND rg.team_code::text = gm.team_code::text
      WHERE rg.dk_points > 0::numeric
      ORDER BY rg.season_year, rg.week, rg.player_pos, rg.dk_points DESC;

## vw_dst

Created by EWT. Selects dst fantasy points on a per-week basis.

    SELECT dst.gsis_id,
    dst.season_year,
    dst.week,
    dst.team_code,
    dst.opp,
    dst.fantasy_points,
    dst.pts_allowed,
    dst.sacks,
    dst.def_td,
    dst.return_td,
    dst."int",
    dst.fum_rec,
    dst.safeties,
    gm.consensus_game_ou AS ou,
    gm.consensus_implied_total AS impltot,
    round(gm.consensus_game_ou - gm.consensus_implied_total, 2) AS opp_impltot,
    gm.is_home,
    gm.is_win,
    wd.weighted_off_dvoa,
    wd.weighted_def_dvoa,
    wd2.weighted_off_dvoa AS opp_weighted_off_dvoa,
    wd2.weighted_def_dvoa AS opp_weighted_def_dvoa
    FROM dst
     LEFT JOIN gamesmeta gm ON dst.gsis_id::text = gm.gsis_id::text AND dst.team_code::text = gm.team_code::text
     LEFT JOIN weekly_dvoa wd ON dst.team_code::text = wd.team_code::text AND dst.season_year = wd.season_year AND dst.week = wd.week
     LEFT JOIN weekly_dvoa wd2 ON dst.opp = wd2.team_code AND dst.season_year = wd2.season_year AND dst.week = wd2.week
    ORDER BY dst.season_year, dst.week, dst.fantasy_points DESC;

## vw_offplays

Created by EWT. Selects all offensive plays.

    CREATE OR REPLACE VIEW public.vw_offplays AS 
     WITH pl AS (
             SELECT play.gsis_id,
                play.drive_id,
                play.play_id,
                play."time",
                play.pos_team,
                play.yardline,
                play.down,
                play.yards_to_go,
                play.description,
                play.note,
                play.time_inserted,
                play.time_updated,
                play.first_down,
                play.fourth_down_att,
                play.fourth_down_conv,
                play.fourth_down_failed,
                play.passing_first_down,
                play.penalty,
                play.penalty_first_down,
                play.penalty_yds,
                play.rushing_first_down,
                play.third_down_att,
                play.third_down_conv,
                play.third_down_failed,
                play.timeout,
                play.xp_aborted
               FROM play
              WHERE (play.gsis_id::text IN ( SELECT game.gsis_id
                       FROM game
                      WHERE game.season_type = 'Regular'::season_phase))
            ), pl2 AS (
             SELECT pl.gsis_id,
                pl.drive_id,
                pl.play_id,
                pl."time",
                pl.pos_team,
                pl.yardline,
                pl.down,
                pl.yards_to_go,
                pl.description,
                pl.note,
                pl.time_inserted,
                pl.time_updated,
                pl.first_down,
                pl.fourth_down_att,
                pl.fourth_down_conv,
                pl.fourth_down_failed,
                pl.passing_first_down,
                pl.penalty,
                pl.penalty_first_down,
                pl.penalty_yds,
                pl.rushing_first_down,
                pl.third_down_att,
                pl.third_down_conv,
                pl.third_down_failed,
                pl.timeout,
                pl.xp_aborted
               FROM pl
              WHERE pl.down = 1 OR pl.down = 2
            UNION ALL
             SELECT pl.gsis_id,
                pl.drive_id,
                pl.play_id,
                pl."time",
                pl.pos_team,
                pl.yardline,
                pl.down,
                pl.yards_to_go,
                pl.description,
                pl.note,
                pl.time_inserted,
                pl.time_updated,
                pl.first_down,
                pl.fourth_down_att,
                pl.fourth_down_conv,
                pl.fourth_down_failed,
                pl.passing_first_down,
                pl.penalty,
                pl.penalty_first_down,
                pl.penalty_yds,
                pl.rushing_first_down,
                pl.third_down_att,
                pl.third_down_conv,
                pl.third_down_failed,
                pl.timeout,
                pl.xp_aborted
               FROM pl
              WHERE pl.down = 3 AND pl.third_down_att = 1
            UNION ALL
             SELECT pl.gsis_id,
                pl.drive_id,
                pl.play_id,
                pl."time",
                pl.pos_team,
                pl.yardline,
                pl.down,
                pl.yards_to_go,
                pl.description,
                pl.note,
                pl.time_inserted,
                pl.time_updated,
                pl.first_down,
                pl.fourth_down_att,
                pl.fourth_down_conv,
                pl.fourth_down_failed,
                pl.passing_first_down,
                pl.penalty,
                pl.penalty_first_down,
                pl.penalty_yds,
                pl.rushing_first_down,
                pl.third_down_att,
                pl.third_down_conv,
                pl.third_down_failed,
                pl.timeout,
                pl.xp_aborted
               FROM pl
              WHERE pl.down = 4 AND pl.fourth_down_att = 1
      ORDER BY 1, 2, 3
            ), pl3 AS (
             SELECT pl2.gsis_id,
                pl2.pos_team,
                count(*) AS plays
               FROM pl2
              GROUP BY pl2.gsis_id, pl2.pos_team
            ), isp AS (
             SELECT pl2.gsis_id,
                pl2.play_id,
                pp.team,
                    CASE
                        WHEN sum(pp.passing_att) >= 1 THEN 1
                        ELSE 0
                    END AS num_pass,
                sum(pp.defense_sk) AS num_sack
               FROM pl2
                 LEFT JOIN play_player pp ON pp.gsis_id::text = pl2.gsis_id::text AND pp.play_id::smallint = pl2.play_id::smallint AND pl2.pos_team::text = pp.team::text
              GROUP BY pl2.gsis_id, pl2.play_id, pp.team
            )
     SELECT isp.gsis_id,
        isp.play_id,
        isp.team,
            CASE
                WHEN (isp.num_pass::double precision + isp.num_sack) > 0::double precision THEN 1
                ELSE 0
            END AS is_pass
       FROM isp
      ORDER BY isp.gsis_id, isp.play_id;

## vw_rushing_tds_1

Created by EWT. Selects all rushing TD from the 1 yardline

    WITH r AS (
      SELECT 
        pp.* 
      FROM 
        play_player AS pp
      WHERE 
        pp.rushing_att > 0
    ),

    pl AS (
      select gsis_id, drive_id, play_id, description, note from play where (yardline).pos >= 49 AND yards_to_go > 0
      order by gsis_id, drive_id, play_id
    ),

    y1r AS (
      SELECT
        pl.*, r.rushing_tds, game.season_year
      FROM pl
      INNER JOIN r
      ON pl.gsis_id = r.gsis_id AND pl.drive_id = r.drive_id AND pl.play_id = r.play_id
      LEFT JOIN game ON pl.gsis_id = game.gsis_id
      ORDER BY gsis_id, drive_id
    )

    SELECT avg(rushing_tds) from y1r

## vw_teamplays

Created by EWT. Selects all team offensive plays on a per-week basis.

    CREATE OR REPLACE VIEW public.vw_teamplays AS 
     WITH g AS (
             SELECT game.gsis_id
               FROM game
              WHERE game.season_type = 'Regular'::season_phase
            ), pl AS (
             SELECT play.gsis_id,
                play.drive_id,
                play.play_id,
                play."time",
                play.pos_team,
                play.yardline,
                play.down,
                play.yards_to_go,
                play.description,
                play.note,
                play.time_inserted,
                play.time_updated,
                play.first_down,
                play.fourth_down_att,
                play.fourth_down_conv,
                play.fourth_down_failed,
                play.passing_first_down,
                play.penalty,
                play.penalty_first_down,
                play.penalty_yds,
                play.rushing_first_down,
                play.third_down_att,
                play.third_down_conv,
                play.third_down_failed,
                play.timeout,
                play.xp_aborted
               FROM play
              WHERE (play.gsis_id::text IN ( SELECT g.gsis_id
                       FROM g))
            ), pl2 AS (
             SELECT pl.gsis_id,
                pl.drive_id,
                pl.play_id,
                pl."time",
                pl.pos_team,
                pl.yardline,
                pl.down,
                pl.yards_to_go,
                pl.description,
                pl.note,
                pl.time_inserted,
                pl.time_updated,
                pl.first_down,
                pl.fourth_down_att,
                pl.fourth_down_conv,
                pl.fourth_down_failed,
                pl.passing_first_down,
                pl.penalty,
                pl.penalty_first_down,
                pl.penalty_yds,
                pl.rushing_first_down,
                pl.third_down_att,
                pl.third_down_conv,
                pl.third_down_failed,
                pl.timeout,
                pl.xp_aborted
               FROM pl
              WHERE pl.down = 1 OR pl.down = 2
            UNION ALL
             SELECT pl.gsis_id,
                pl.drive_id,
                pl.play_id,
                pl."time",
                pl.pos_team,
                pl.yardline,
                pl.down,
                pl.yards_to_go,
                pl.description,
                pl.note,
                pl.time_inserted,
                pl.time_updated,
                pl.first_down,
                pl.fourth_down_att,
                pl.fourth_down_conv,
                pl.fourth_down_failed,
                pl.passing_first_down,
                pl.penalty,
                pl.penalty_first_down,
                pl.penalty_yds,
                pl.rushing_first_down,
                pl.third_down_att,
                pl.third_down_conv,
                pl.third_down_failed,
                pl.timeout,
                pl.xp_aborted
               FROM pl
              WHERE pl.down = 3 AND pl.third_down_att = 1
            UNION ALL
             SELECT pl.gsis_id,
                pl.drive_id,
                pl.play_id,
                pl."time",
                pl.pos_team,
                pl.yardline,
                pl.down,
                pl.yards_to_go,
                pl.description,
                pl.note,
                pl.time_inserted,
                pl.time_updated,
                pl.first_down,
                pl.fourth_down_att,
                pl.fourth_down_conv,
                pl.fourth_down_failed,
                pl.passing_first_down,
                pl.penalty,
                pl.penalty_first_down,
                pl.penalty_yds,
                pl.rushing_first_down,
                pl.third_down_att,
                pl.third_down_conv,
                pl.third_down_failed,
                pl.timeout,
                pl.xp_aborted
               FROM pl
              WHERE pl.down = 4 AND pl.fourth_down_att = 1
      ORDER BY 1, 2, 3
            ), pl3 AS (
             SELECT pl2.gsis_id,
                pl2.pos_team,
                count(*) AS plays
               FROM pl2
              GROUP BY pl2.gsis_id, pl2.pos_team
            )
     SELECT gm.gsis_id,
        gm.season_year,
        gm.week,
        gm.game_date,
        gm.team_code,
        gm.opp,
        gm.s,
        gm.is_ot,
        gm.consensus_implied_total,
        gm.is_home,
        gm.is_win,
        pl3.plays
       FROM gamesmeta gm
         LEFT JOIN pl3 ON gm.gsis_id::text = pl3.gsis_id::text AND gm.team_code::text = pl3.pos_team::text
      WHERE gm.season_year > 2008
      ORDER BY gm.gsis_id;

## weekly_stats

Created by EWT. Aggregates play_player into weekly totals for each player.

CREATE MATERIALIZED VIEW public.weekly_stats AS 
 SELECT g.season_year,
    g.week,
    p.full_name,
    p."position",
    fpts_std(aggwt.*) AS fpts_std,
    fpts_ppr(aggwt.*) AS fpts_ppr,
    fpts_dk(aggwt.*) AS fpts_dk,
        CASE
            WHEN aggwt.team::text = g.home_team::text THEN g.away_team
            ELSE g.home_team
        END AS opp,
    aggwt.gsis_id,
    aggwt.player_id,
    aggwt.team,
    aggwt.passing_cmp,
    aggwt.passing_att,
    aggwt.passing_yds,
    aggwt.passing_int,
    aggwt.passing_tds,
    aggwt.passing_twoptm,
    aggwt.rushing_att,
    aggwt.rushing_yds,
    aggwt.rushing_tds,
    aggwt.rushing_twoptm,
    aggwt.receiving_tar,
    aggwt.receiving_rec,
    aggwt.receiving_yds,
    aggwt.receiving_tds,
    aggwt.receiving_twoptm,
    aggwt.fumbles_lost,
    aggwt.fumbles_rec_tds,
    aggwt.puntret_tds,
    aggwt.kickret_tds
   FROM game_agg aggwt
     JOIN player p ON aggwt.player_id::text = p.player_id::text
     JOIN game g ON aggwt.gsis_id::text = g.gsis_id::text
  WHERE p."position" = ANY (ARRAY['WR'::player_pos, 'QB'::player_pos, 'TE'::player_pos, 'RB'::player_pos, 'UNK'::player_pos])
WITH DATA;
