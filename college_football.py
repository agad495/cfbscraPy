import requests
import pandas as pd
import numpy as np
import json
from pandas import json_normalize

class CollegeFootball():
    """A class to pull and clean data from the college football data api"""
    def __init__(self):
        self.site = 'https://api.collegefootballdata.com/'
    
    def season_pbp(self, year=2019, week_start=1, week_end=15, season_type='regular'):
        """Pulls play-by-play data for a given year"""
        url = [self.site + 'plays?seasonType=' + str(season_type) + '&year=' + 
               str(year) + '&week=' + str(wk) for wk in range(week_start, week_end)]
        cfbyear = None
        for wk in url:
            cfbdata = requests.get(wk)
            data = cfbdata.json()
            with open('cfbdata.json', 'w') as json_file:
                json.dump(data, json_file)
            cfbwk = pd.read_json('cfbdata.json', orient = 'columns')
            cfbyear = pd.concat([cfbyear, cfbwk])
        return cfbyear
    
    def pred_pts(self, down):
        """Pulls predicted points data for all yard lines and distances for a 
        given down. To pull all four downs, use [pred_pts(i) for i in range(1,5)]"""
        url = [self.site + 'ppa/predicted?down=' + str(down) + '&distance=' + str(dist) for dist in range(1,100)]
        cfbyear = []
        togo = 1
        for dist in url:
            cfbdata = requests.get(dist)
            data = cfbdata.json()
            for d in data:
                d['down'] = down
                d['distance'] = togo
            cfbyear.append(data)
            togo += 1
        return cfbyear
    
    def team_profiles(self, season_pbp, ppp):
        ncaa_std = season_pbp.loc[(season_pbp.play_type == 'Rush') | (season_pbp.play_type == 'Sack') |
                          (season_pbp.play_type == 'Pass Reception') | (season_pbp.play_type == 'Pass Incompletion') |
                          (season_pbp.play_type == 'Fumble Recovery (Opponent)') | (season_pbp.play_type == 'Passing Touchdown') |
                          (season_pbp.play_type == 'Rushing Touchdown') | (season_pbp.play_type == 'Pass Interception Return') |
                          (season_pbp.play_type == 'Fumble Recovery (Own)') | (season_pbp.play_type == 'Interception Return Touchdown') |
                          (season_pbp.play_type == 'Fumble Return Touchdown') | (season_pbp.play_type == 'Safety')]
        ncaa_std = ncaa_std.dropna()
        ncaa_std = ncaa_std.loc[(ncaa_std.period == 1) |
                           ((ncaa_std.period == 2) & (abs(ncaa_std.defense_score - ncaa_std.offense_score) <= 36)) |
                           ((ncaa_std.period == 3) & (abs(ncaa_std.defense_score - ncaa_std.offense_score) <= 26)) |
                           ((ncaa_std.period == 4) & (abs(ncaa_std.defense_score - ncaa_std.offense_score) <= 20))]
        ncaa_std['yard_line'] = np.where(ncaa_std.offense == ncaa_std.away, 100 - ncaa_std.yard_line, ncaa_std.yard_line)
        ncaa_std['yard_line'] = np.where(ncaa_std.yard_line == 100, 99, ncaa_std.yard_line)
        ncaa_std['yard_line'] = np.where(ncaa_std.yard_line == 0, 1, ncaa_std.yard_line)
        ncaa_std['distance'] = np.where(ncaa_std.distance == 0, 1, ncaa_std.distance)
        ncaa_std['yard_line'] = np.where(ncaa_std.yard_line + ncaa_std.distance > 100, 100 - ncaa_std.yard_line, ncaa_std.yard_line)
        ncaa_std['yards_dist'] = ncaa_std['yards_gained'] / ncaa_std['distance']
        ncaa_std['success'] = np.where(((ncaa_std.down == 1) & (ncaa_std.yards_dist >= 0.5)) | ((ncaa_std.down == 2) & (ncaa_std.yards_dist >= 0.7)) |
                                   ((ncaa_std.down >= 3) & (ncaa_std.yards_dist >= 1)), 1, 0)
        ncaa_std['success'] = np.where((ncaa_std.play_type == 'Sack') | (ncaa_std.play_type == 'Pass Incompletion') |
                                  (ncaa_std.play_type == 'Fumble Recovery (Opponent)') | (ncaa_std.play_type == 'Fumble Recovery (Own)') |
                                  (ncaa_std.play_type == 'Pass Interception') | (ncaa_std.play_type == 'Interception Return Touchdown') |
                                  (ncaa_std.play_type == 'Fumble Return Touchdown') | (ncaa_std.play_type == 'Safety'), 0, ncaa_std.success)
        ncaa_success = ncaa_std.groupby(['offense']).agg({'success':'mean'})
        ncaa_success.columns = ['offense success']
        ncaa_success['o success rank'] = ncaa_success['offense success'].rank(pct=True)
        ncaa_passing = ncaa_std[ncaa_std.play_text.str.contains('pass')]
        ncaa_pass_sr = ncaa_passing.groupby(['offense']).agg({'success':'mean'})
        ncaa_pass_sr.columns = ['passing o success']
        ncaa_pass_sr['pass o success rank'] = ncaa_pass_sr['passing o success'].rank(pct=True)
        ncaa_rushing = ncaa_std[ncaa_std.play_text.str.contains('run')]
        ncaa_rush_sr = ncaa_rushing.groupby(['offense']).agg({'success':'mean'})
        ncaa_rush_sr.columns = ['rushing o success']
        ncaa_rush_sr['rush o success rank'] = ncaa_rush_sr['rushing o success'].rank(pct=True)
        ncaa_o_success = ncaa_success.join(ncaa_pass_sr)
        ncaa_o_success = ncaa_o_success.join(ncaa_rush_sr)
        ncaa_success_d = ncaa_std.groupby(['defense']).agg({'success':'mean'})
        ncaa_success_d.columns = ['defense success']
        ncaa_success_d['d success rank'] = ncaa_success_d['defense success'].rank(pct=True)
        ncaa_pass_sr_d = ncaa_passing.groupby(['defense']).agg({'success':'mean'})
        ncaa_pass_sr_d.columns = ['passing d success']
        ncaa_pass_sr_d['pass d success rank'] = ncaa_pass_sr_d['passing d success'].rank(pct=True)
        ncaa_rush_sr_d = ncaa_rushing.groupby(['defense']).agg({'success':'mean'})
        ncaa_rush_sr_d.columns = ['rushing d success']
        ncaa_rush_sr_d['rush d success rank'] = ncaa_rush_sr_d['rushing d success'].rank(pct=True)

        ncaa_d_success = ncaa_success_d.join(ncaa_pass_sr_d)
        ncaa_d_success = ncaa_d_success.join(ncaa_rush_sr_d)

        ncaa_iso = ncaa_std.loc[ncaa_std.success == 1]
        ncaa_isoppp = ncaa_iso.groupby(['offense']).agg({'ppa':'mean'})
        ncaa_isoppp.columns = ['offense isoppp']
        ncaa_isoppp['o isoppp rank'] = ncaa_isoppp['offense isoppp'].rank(pct=True)
        ncaa_iso_pass = ncaa_iso[ncaa_iso.play_text.str.contains('pass')]
        ncaa_iso_pass_o = ncaa_iso_pass.groupby(['offense']).agg({'ppa':'mean'})
        ncaa_iso_pass_o.columns = ['pass o isoppp']
        ncaa_iso_pass_o['pass o isoppp rank'] = ncaa_iso_pass_o['pass o isoppp'].rank(pct=True)
        ncaa_iso_rush = ncaa_iso[ncaa_iso.play_text.str.contains('run')]
        ncaa_iso_rush_o = ncaa_iso_rush.groupby(['offense']).agg({'ppa':'mean'})
        ncaa_iso_rush_o.columns = ['rush o isoppp']
        ncaa_iso_rush_o['rush o isoppp rank'] = ncaa_iso_rush_o['rush o isoppp'].rank(pct=True)
        ncaa_o_iso = ncaa_isoppp.join(ncaa_iso_pass_o)
        ncaa_o_iso = ncaa_o_iso.join(ncaa_iso_rush_o)
        ncaa_isoppp_d = ncaa_iso.groupby(['defense']).agg({'ppa':'mean'})
        ncaa_isoppp_d.columns = ['defense isoppp']
        ncaa_isoppp_d['d isoppp rank'] = ncaa_isoppp_d['defense isoppp'].rank(pct=True)
        ncaa_iso_pass_d = ncaa_iso_pass.groupby(['defense']).agg({'ppa':'mean'})
        ncaa_iso_pass_d.columns = ['pass d isoppp']
        ncaa_iso_pass_d['pass d isoppp rank'] = ncaa_iso_pass_d['pass d isoppp'].rank(pct=True)
        ncaa_iso_rush_d = ncaa_iso_rush.groupby(['defense']).agg({'ppa':'mean'})
        ncaa_iso_rush_d.columns = ['rush d isoppp']
        ncaa_iso_rush_d['rush d isoppp rank'] = ncaa_iso_rush_d['rush d isoppp'].rank(pct=True)
        ncaa_d_iso = ncaa_isoppp_d.join(ncaa_iso_pass_d)
        ncaa_d_iso = ncaa_d_iso.join(ncaa_iso_rush_d)
        ncaa_std['run_attempt'] = np.where(ncaa_std.play_text.str.contains('run'), 1, 0)
        ncaa_sdowns = ncaa_std.loc[(ncaa_std.down == 1) | ((ncaa_std.down == 2) & (ncaa_std.distance < 8)) | ((ncaa_std.down >= 3) & (ncaa_std.distance < 5))]
        ncaa_sdowns_run = ncaa_sdowns.groupby(['offense']).agg({'run_attempt':'mean'})
        ncaa_sdowns_run.columns = ['std downs run rate']
        ncaa_pdowns = ncaa_std.loc[((ncaa_std.down == 2) & (ncaa_std.distance >= 8)) | ((ncaa_std.down >= 3) & (ncaa_std.distance >= 5))]
        ncaa_pdowns_run = ncaa_pdowns.groupby(['offense']).agg({'run_attempt':'mean'})
        ncaa_pdowns_run.columns = ['pass downs run rate']
        ncaa_offense = ncaa_o_success.join(ncaa_o_iso)
        ncaa_offense = ncaa_offense.join(ncaa_sdowns_run)
        ncaa_offense = ncaa_offense.join(ncaa_pdowns_run)
        ncaa_defense = ncaa_d_success.join(ncaa_d_iso)
        ncaa_team = ncaa_offense.join(ncaa_defense)
        return ncaa_team
    
    def player_game_logs(self, year=2019, week_start=1, week_end=15, season_type='regular'):
        """Pulls play-by-play data for a given year"""
        url = [self.site + 'games/players?year=' + str(year) + '&week=' + 
               str(wk) + '&seasonType=' + str(season_type) for wk in range(week_start, week_end)]
        playeryear = None
        for wk in url:
            playerdata = requests.get(wk)
            data = playerdata.json()
            with open('playerdata.json', 'w') as json_file:
                json.dump(data, json_file)
            playerwk = pd.read_json('playerdata.json', orient = 'columns')
            playeryear = pd.concat([playeryear, playerwk])
        return playeryear

    def betting_lines(self, year=2019, week_start=1, week_end=15, season_type='regular'):
        """Pulls spread and over/under data for a given year/week"""
        if week_end == None:
            w_e = week_start + 1
        else:
            w_e = week_end
        url = [self.site + 'lines?year=' + str(year) + '&week=' + 
               str(wk) + '&seasonType=' + str(season_type) for wk in range(week_start, w_e)]
        bets = None
        for wk in url:
            bettingdata = requests.get(wk)
            data = bettingdata.json()
            with open('bettingdata.json', 'w') as json_file:
                json.dump(data, json_file)
            bettingwk = pd.read_json('bettingdata.json', orient = 'records')
            bets = pd.concat([bets, bettingwk])
        return bets
    
    def basic_game_info(self, year=2019, week_start=1, week_end=15, 
                        season_type='regular', team=None, ht=None, at=None,
                        conf=None, gameid=None):
        '''Pulls basic game info such as GameID, Pts, Win Expectancy, Excitement Index, etc'''
        if team is not None:
            team = f'&team={team}'
        else:
            team = ''
        if ht is not None:
            ht = f'&home={ht}'
        else:
            ht = ''
        if at is not None:
            at = f'&away={at}'
        else:
            at = ''
        if conf is not None:
            conf = f'&conference={conf}'
        else:
            conf = ''
        if gameid is not None:
            gameid = f'&id={gameid}'
        else:
            gameid = ''

        if week_end == None:
            w_e = week_start + 1
        else:
            w_e = week_end
            
        url = [self.site + 'games?year=' + str(year) + '&week=' + 
               str(wk) + '&seasonType=' + str(season_type) +
               team + ht + at + conf + gameid for wk in range(week_start, w_e)]
        
        games = None
        for wk in url:
            gamedata = requests.get(wk)
            data = gamedata.json()
            with open('gamedata.json', 'w') as json_file:
                json.dump(data, json_file)
            gamewk = pd.read_json('gamedata.json', orient = 'records')
            games = pd.concat([games, gamewk])
        return games
    
    def advanced_box_score(self, gameid, unit='teams', period='total'):
        '''Pulls the advanced box score for a given game'''
        url = f'{self.site}game/box/advanced?gameId={gameid}'
        box_data = requests.get(url)
        data = box_data.json()
        with open('box_data.json', 'w') as json_file:
            json.dump(data, json_file)
        box_score = pd.read_json('box_data.json', orient = 'records')
        
        advanced = pd.DataFrame()
        if unit == 'teams':
            for i in range(6):
                stat = pd.DataFrame(box_score.iloc[i, 0])
                new_cols = []
                if (i==0):
                    cols = stat.columns
                    for column in cols:
                        column = f'{column}_explosive'
                        new_cols.append(column)
                    stat.columns = new_cols
                elif (i==3):
                    cols = stat.columns
                    for column in cols:
                        column = f'{column}_ppa'
                        new_cols.append(column)
                    stat.columns = new_cols
                advanced = pd.concat([advanced, stat.reset_index(drop=True)], axis=1)
            advanced.drop(['team_explosive', 'team_ppa'], axis=1, inplace=True)                
            explosive = json_normalize(advanced['overall_explosive'])['total']
            ppa_o = json_normalize(advanced['overall_ppa'])['total']
            ppa_p = json_normalize(advanced['passing_ppa'])['total']
            ppa_r = json_normalize(advanced['rushing_ppa'])['total']
            advanced['overall_explosive'] = explosive
            advanced['overall_ppa'] = ppa_o
            advanced['passing_ppa'] = ppa_p
            advanced['rushing_ppa'] = ppa_r
            
        else:
            for i in [3, 7]:
                stat = pd.DataFrame(box_score.iloc[i, 0])
                stat.index = stat.player
                advanced = pd.concat([advanced, stat], axis=1)
        advanced = advanced.loc[:, ~advanced.columns.duplicated()]
            
        return advanced
    
    def team_recruiting(self, year=2019, team=None):
        if team is not None:
            team = f'&team={team}'
        else:
            team = ''
        url = f'{self.site}recruiting/teams?year={year}{team}'
        recruit_data = requests.get(url)
        data = recruit_data.json()
        with open('recruit_data.json', 'w') as json_file:
            json.dump(data, json_file)
        recruiting = pd.read_json('recruit_data.json')
        
        return recruiting
    
    def player_recruiting(self, year=2019, classification='HighSchool',
                          pos=None, state=None, team=None):
        '''Scrapes individual recruit data'''
        if pos:
            pos = f'&position={pos}'
        else:
            pos = ''
        if state:
            state = f'&state={state}'
        else:
            state = ''
        if team:
            team = f'&state={state}'
        else:
            team = ''
        url = f'{self.site}recruiting/players?year={year}&classification={classification}' \
        f'{pos}{state}{team}'
        
        recruits = requests.get(url)
        data = recruits.json()
        player_recruiting = pd.DataFrame(data)
        
        return player_recruiting
        
    
    def game_wpa(self, gameID, spreadAdj = 'false'):
        '''Scrapes game Win Probability data. Set spreadAdj to True to take the
        pregame spread into account'''
        url = f'{self.site}metrics/wp?gameId={gameID}&adjustForSpread={spreadAdj}'
        wpa_data = requests.get(url)
        data = wpa_data.json()
        wpa = pd.DataFrame(data)
        
        return wpa
    
    def player_usage(self, year=2019, team=None, conf=None, pos=None,
                     player_id=None, garbageTime='false'):
        '''Scrapes player usage data'''
        if pos:
            pos = f'&position={pos}'
        else:
            pos = ''
        if conf:
            conf = f'&conference={conf}'
        else:
            conf = ''
        if team:
            team = f'&team={team}'
        else:
            team = ''
        if player_id:
            player_id = f'&playerId={player_id}'
        else:
            player_id = ''
        url = f'{self.site}player/usage?year={year}&excludeGarbageTime={garbageTime}' \
        f'{team}{pos}{conf}{player_id}'
        player_use_data = requests.get(url)
        data = player_use_data.json()
        pud = pd.DataFrame(data)
        
        usages = json_normalize(pud['usage'])
        user = pd.concat([pud.drop('usage', axis=1), usages], axis=1)
        
        return user
        
    def player_pbp(self, year=2019, week=None, team=None, gameid=1, 
                   playerid=None, statType=None, sznType=None):
        if week:
            week = f'&week={week}'
        else:
            week = ''
        if team:
            team = f'&team={team}'
        else:
            team = ''
        if playerid:
            playerid = f'&playerId={playerid}'
        else:
            playerid = ''
        if statType:
            statType = f'&statTypeId={statType}'
        else:
            statType = ''
        if sznType:
            sznType = f'&seasonType={sznType}'
        else:
            sznType = ''
        if gameid == 1:
            gameids = self.basic_game_info(year=year)['id']
            urls = [f'{self.site}play/stats?year={year}{week}{team}&gameId={games}{playerid}'
            f'{statType}{sznType}' for games in gameids]
            playa = pd.DataFrame()
            for g in urls:
                player_data = requests.get(g)
                data = player_data.json()
                playa = playa.append(pd.DataFrame(data))
        elif gameid > 1:
            url = f'{self.site}play/stats?year={year}{week}{team}&gameId={gameid}{playerid}' \
            f'{statType}{sznType}'
            player_data = requests.get(url)
            data = player_data.json()
            playa = pd.DataFrame(data)

        else:
            gameid = ''
            url = f'{self.site}play/stats?year={year}{week}{team}{gameid}{playerid}' \
            f'{statType}{sznType}'
            player_data = requests.get(url)
            data = player_data.json()
            playa = pd.DataFrame(data)


        
        return playa