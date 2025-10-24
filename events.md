# Events that signal the end of a possession

Using the event_mappings comment, we go through play-by-play and get the outcomes of possessions. 

For now, we'll just do the team. 

For subbing out, each game is split into every period (usually just four quarters). Then, anytime a player gets a stat, we know they were playing since beginning. Same for subbing out (retrospective). Otherwise we just use subbing in to mark when a player started and subbing out when they left. 