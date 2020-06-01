# cfbscraPy
Easily pull data from the collegefootballdata.com API

Creating a class instance:
```
from cfbscraPy import CollegeFootball
cfb = CollegeFootball()
```

Scraping play-by-play data for a given season or week:
```
pbp19 = cfb.season_pbp(year=2019, week_start=1, week_end=15, season_type='regular')
```

Build team profiles (consisting of success rate, isoppp, ect.) using scraped play-by-play data and epa data:
```
pbp19 = cfb.season_pbp(year=2019)
epa = [cfb.pred_pts(i) for i in range(1,5)]
ncaa2019 = cfb.team_profiles(pbp19, epa)
```

Scrape betting lines for a given year or week:
```
lines19 = cfb.betting_lines(year=2019, week_start=1, week_end=15, season_type='regular')
```

Scrape basic game info (excitement index, game id, win %, points, etc.):
```
basic_games19 = cfb.basic_game_info(year=2019, week_start=1, week_end=15, 
                        season_type='regular', team=None, ht=None, at=None,
                        conf=None, gameid=None)
```

Get advanced box score data for a given game id:
```
adv_box_score = cfb.advanced_box_score(gameid=401110723)
```

Get recruiting data by team and by player for a given year:
```
team_recruiting19 = cfb.team_recruiting(year=2019)
recruits19 = cfb.player_recruiting(year=2019, classification='HighSchool',
                          pos=None, state=None, team=None)
```
The ```player_recruiting()``` function can scrape for a given position, state and/or college team using the optional inputs.

Get win probability added play-by-play data for a given game (use spread_adjust = 'true' to adjust win probability added values for the pregame consensus spread:
```
wpa19 = cfb.game_wpa(gameID=401110723, spreadAdj = 'false')
```

