Set up:
- Create main dir
- git clone espn-api
- git clone espn-fantasy-project
- run 'uv sync' in espn-fantasy-project
- if there is a cloud sync error, then run 'uv sync --link-mode=copy'
- create .env file in espn-fantasy-project/python

.env file:
ESPN_LEAGUE_ID = <espn league id>
ESPN_YEAR = <year>
ESPN_S2 = <'espn_s2'>
ESPN_SWID = <'{espn_swid}'>