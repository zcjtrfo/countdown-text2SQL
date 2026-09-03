import streamlit as st
import sqlite3
import pandas as pd
import json # <-- NEW IMPORT
from google import genai

# --- 1. CONFIGURATION & AUTHENTICATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    st.error("API Key not found. Please configure Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

TERMINOLOGY = """
14 round format – format involving eight letters games, four numbers games and two conundrums. It was used between Series 2 and Series 45, uniquely for grand finals and specials. This is the same format used by the original French show Des chiffres et des lettres, although the rounds are not in the same order.
15 round format (new) – the revised 15 round format introduced during Series 68, consisting of 10 letters games, four numbers games and one conundrum.
15 round format (old) – the original 15 round format consisting of 11 letters games, three numbers games and one conundrum. Used from Series 46 until early in Series 68.
480 club – informal name for the players that scored at least 480 points as an Octochamp during their runs under the 9 round format.
800/900/1000 club – informal name for the players that have scored at least 800/900/1000 points as an Octochamp during their runs under the 15 round format.
9 round format – the original format, consisting of six letters games, two numbers games and one conundrum. Was used between Series 1 and Series 45.
Ambulance - used when a contestant scores 3 consecutive nines. To date, there is only one known occurrence, in Episode 5654.
Arithmetician – the member of the presenting team that provides solutions to the numbers rounds if such a solution evades the contestants, and also puts up the letters and numbers.
CECIL – Countdown's Electronic Calculator in Leeds, the computer that generates the random numbers between 100 and 999 for the numbers games. (Although the show is now filmed in Manchester, this term is still used).
Century – a score of 100 or more. This is quite common under the 15 round system, but also happened in the 14 round finals, first achieved by Clive Spate in Series 6.
Contestant – a Countdown player, someone who appears on Countdown as a player.
Conundrum – the nine-letter anagram at the end of the show. Players buzz in with the right answer, only the player that buzzes in first with the right answer gets the 10 points. If the player gets it wrong, the other player has the rest of the 30 seconds to buzz in.
Darren – a word which is the longest in that given round, and the only word of that length. For instance, from the selection ACELOPQST, POLECATS would be the only eight-letter word.
Dictionary Corner – a special celebrity guest and a lexicographer together working to find the best words in selections where the contestants don't get the longest possible word. They're often helped by the show's producers, led by Damian Eadie, by way of an earpiece. The guest also gives a short anecdote between Rounds 6 and 7.
Goody bag – the prize received by all contestants, currently consisting of a Countdown mug, a pair of Countdown pens, a Countdown clock, Oxford Dictionary of English Third Edition, and Susie Dent's Modern Tribes. A teapot is included for contestants that win at least one game.
Final / Grand final – the final game of each standard series, with the two players who have won their quarter-final and semi-final facing off to be a series champion. Until Series 46 this was a 14 round game, now it's always a 15 round game.
Heats / prelims - the episodes of each standard series which are not part of the series finals. The winning contestant (the champion) stay on to the next episode where they play a new contestant (the challenger). If a player wins 8 prelim episodes, they retire as an octochamp and two new contenstants appear on the next episode.
The (series) finals - the seven episodes at the end of each regular series which determine the series champion in knockout format (four Quarterfinals, two Semifinals, one Grand Final)
Dictionary Corner Guest – a celebrity guest invited on to Countdown for one day's filming (usually five shows). They help find the longest words in the letters rounds, and give a short anecdote between Rounds 6 and 7.
Letters round – a round using nine letters where the contestants make the longest word they can, using each letter no more than once. Words must be in Oxford Dictionaries Online.
Lexicographer – a resident expert who helps to find the longest words from the letters games, with the help of a celebrity guest.
Max game – a game in which the best possible score is achieved in every single round
Numbers round – a round using six randomly chose numbers between 1 and 100 and a target between 100 and 999. The aim is to use the six numbers once each to make the target number using the four basic mathematical operations (addition, division, subtraction and multiplication). The numbered cards available are 1 to 10 twice each, 25, 50, 75 and 100.
Octochamp – a player who wins eight consecutive prelim episodes without being defeated. Eight episodes is the maximum, and after that the player retires unbeaten (usually appearing again in the series finals).
Octorun - a player's run of 8 consecutive wins in prelim episodes, thereby becoming an Octochamp.
Octototal - a player's total score across their 8 prelim wins as an Octochamp.
Oxford Dictionaries Online (ODO) – the official dictionary used to judge words on Countdown since Series 71.
Oxford Dictionary of English (ODE) – the dictionary used to judge words on Countdown from Series 43 to Series 70, produced by Oxford University Press.
Pencam – a small camera shaped like a pen, which used to display words found in the dictionary from Series 22 until Series 70.
Phantom – a letter seen by a contestant although not actually in the selection. For example, declaring COUNTDOWN from DDNNOOTUW would be a result of seeing a "phantom C".
Raw score – a scoring system whereby one's opponent's scores are ignored, as if they were playing on their own.
Series – a sequence of over 100 episodes with just one eventual winner at the end. A series winner is a player that wins the grand final of a series.
Teapot – the individual prize for a player that wins an episode.
Viscount – in Series 46, players were only permitted to win six games maximum instead of eight, the name Octochamp was not suitable for these players as the octo- is a reference to eight. So the players were called Viscounts, with reference to VI meaning six in Roman numerals, and -count referring to Countdown.
Xicount – an unofficial term for players who become Octochamps and then go on to win their series, giving them a total of 11 wins, the maximum possible in a single series. Xicount is from XI meaning 11 in Roman numerals, and -count referring to Countdown.
"""

# --- 2. THE DATABASE SCHEMA ---
SCHEMA_TEXT = """
Notes
At the time of writing, the database contains details for games up to the end of Series 87, which is all episodes up to and including 29th June 2023.

There are imperfections and caveats to bear in mind when using this data.

Incompleteness
Some episode details are incomplete or totally absent. For series 1, scores for most of the games are not known. For series 2, most of the game scores and round selections are known, but not the contestants' offerings. Information for series 3 onwards is mostly complete apart from series 7, for which only a few episodes have known round details.

A NULL value for any field in a table means the information is not available or not applicable.

Historical letters round maxes
The recaps on the wiki were generated with the recap writer. The recap writer does not know about dictionaries earlier than the ODE2r, and this affects the accuracy of the maximum for a letters round. Episodes from before the adoption of the ODE2r (that is, prior to 29th May 2006) have their maxes calculated according to the ODE2r. This means max scores for letters rounds earlier than this date may not be accurate.

Data duplication
The database schema sometimes stores redundant information. For example, for each round, the score each player achieved in that round is stored, as well as the cumulative score for the player so far in the game. It's not strictly necessary to store the cumulative score because that can be derived from the sum of the round scores, but it is stored for ease of use so that queries don't have to recalculate it every time.

Excluded episodes
Catsdown episodes are not included.

Episodes from the 1998 Celebrity Countdown series are not included. Not sure why.

Mistakes
Various consistency checks have been run against the data to check for any nonsense situations, such as a player not appearing to receive the right number of points for their declaration, a player receiving anything other than 0 or 10 points for a conundrum, the final score for a game not agreeing with what it should be from the round-by-round scores, and so on. This originally found dozens of errors, most of which were found to be mistakes on the wiki caused by arithmetic errors from manually-generated recaps. I fixed those errors on the wiki a while ago.

In rare cases, a scoring mistake was made on the show so the database preserves it, such as in round 10 of this game.

There are almost certainly other mistakes, probably mine, waiting to be found.

Miscellaneous
In some cases, we know the answer to the conundrum but not the exact scramble. In these cases, the scramble recorded in the database contains the letters of the conundrum in alphabetical order.
If a contestant offered more than one word in a letters round, which was quite common in the early years of the show, the database only recognises the first word. For example, in round 2 of this episode, C2's word is taken as FARMER and the others are ignored.
Tables
The base tables that comprise the database are described here. The database I use has other tables, but I haven't included those because most of them were created only to answer a particular question and can be derived from the tables listed below anyway.

PERSON
A row in the PERSON table represents a person who has appeared on Countdown as a contestant, lexicographer or DC guest. A person should only have one entry in this table, and hence only one ID, even if they have appeared in more than one different capacity. For example, Damian Eadie the contestant and Damian Eadie the lexicographer are the same person, so have the same ID.

Definition
CREATE TABLE person (
	id         int primary key,
	name       text not null,
	page_title text not null
);
A person's name isn't sufficient to identify a person. Different people with the same name have appeared on the show: for example, there have been two players called Chris Davies and three called Mike Brown. The opposite problem also exists: some players have used different names in different appearances, for example Edward McCullagh and Ed McCullagh, and Saladin Khoshnaw and Karl Kurdistan.

So the id field, which is a number, is unique to a person and never reused or changed. The script which assigned IDs to players started from series 1 and worked forwards, so person IDs are for the most part assigned sequentially based on the date of their first appearance, with the occasional exception for boring technical reasons.

The name field could be any name the person has used on the programme, but in practice it usually ends up being the earliest name on a series recap page on the wiki.

The page_title column can be appended onto http://wiki.apterous.org/ to find that player's wiki page. The scripts which convert the wiki into database tables use the links to players' pages on the series recap page to tell apart players with the same name. For example, the links to Chris Davies' page on the series 61 page point to http://wiki.apterous.org/Chris_Davies_(Series_61), but the links to the player with the same name in series 59 point to http://wiki.apterous.org/Chris_Davies_(Series_59), and that's how the database-building script knew they were two different players so needed two different person IDs. Although the page to which a player's link points uniquely identifies which player it is, this isn't used as the primary key, in case someone's page title changes. The page_title field isn't much practical use to users of the database unless you want to generate links to players' wiki pages.

FORMAT
Lists all the episode formats. The id field is used by the GAME table. The format IDs are supposed to make some kind of sense.

Definition
CREATE TABLE format (
	id	int primary key,
	name	text not null,
	rounds	text not null
);
Values
id	name	rounds
-15	Masters	LNCLNCLNCLNCLNC
9	9 rounder	LLLNLLLNC
12	12 rounder	LLLNLLLNLLNC
14	14 rounder	LLNLLNCLLNLLNC
15	Old 15 rounder	LLLLNLLLLNLLLNC
150	15 rounder	LLNLLNLLNLLLLNC
SERIES
The GAME table has a series field, which refers to the id field of this table.

Definition
CREATE TABLE series (
	id      int primary key,   -- primary key
	name    text not null      -- name of series, e.g. "Series 69"
);
GAME
Every row in the GAME table refers to one Countdown match. Normally this corresponds to one episode, except for the Masters games which were spread over five episodes each. Game scores and players are stored in the GAME_PLAYER table.

Definition
CREATE TABLE game (
	ep_id     text not null,               -- primary key: episode ID used by the wiki
	series    int references series(id),   -- series ID: foreign key into SERIES table
	ep_type   text not null,               -- episode type code (see below)
	format    int references format(id),   -- format: foreign key into FORMAT table
	tx_date   text,                        -- first broadcast date (NULL if unbroadcast)
	tiebreak  int,                         -- 1 if this game went to a tiebreak, 0 if not
	max_score int,                         -- maximum possible score in this game
	primary key (ep_id)
);
tx_date may be NULL if the episode was never broadcast. tiebreak and max_score may be NULL if these details are not known.

The ep_type field is a short code defining what kind of episode this is. These codes come from the wiki. At present the codes used are:

ep_type	Description
P	Preliminary (ordinary series game)
QP	Qualifying preliminary (series last 16, rarely used)
QF	Series quarter-final
SF	Series semi-final
GF	Series final
Masters 1	Masters series 1
Masters 2	Masters series 2
CP	Championship of Champions last 16
CQF	Championship of Champions quarter-final
CSF	Championship of Champions semi-final
CGF	Championship of Champions final
30BP	30th Birthday Championship preliminary round
30B1	30th Birthday Championship last 32
30B2	30th Birthday Championship last 16
30BQF	30th Birthday Championship quarter-final
30BSF	30th Birthday Championship semi-final
30BGF	30th Birthday Championship final
xQF	Supreme Championship group x quarter-final
xSF	Supreme Championship group x semi-final
xGF	Supreme Championship group x final
SQF	Supreme Championship quarter-final
SSF	Supreme Championship semi-final
SGF	Supreme Championship final
JSF	Junior Championship semi-final
JF	Junior Championship final
LSF	Ladies' Championship semi-final
LF	Ladies' Championship final
S	Special episode
X	Christmas episode
Examples
The 30th birthday championship final:

ep_id	series	ep_type	format	tx_date	tiebreak	max_score
5654	-19	30BGF	15	2013-03-01	0	149
GAME_PLAYER
A row in this table represents one player in one game. So there are two rows in this table for every game, provided the identities of the players are known.

Definition
CREATE TABLE game_player (
	ep_id	text not null references game(ep_id),  -- episode ID: foreign key into GAME table
	seat	int,                                   -- which seat the player sat in: 1 is camera left (champion's chair), 2 is camera right (challenger's chair)
	p_id	int references person(id),             -- player ID: foreign key into PERSON table
	name	text,                                  -- name the player used for this episode
	score	int,                                   -- this player's final score in this episode
	primary key (ep_id, p_id),
	unique (ep_id, seat)
);
Examples
The 30th Birthday Championship final has the following two rows associated with it.

ep_id	seat	p_id	name	score
5654	1	4889	Jack Hurst	111
5654	2	3733	Conor Travers	146
GAME_GUEST
An entry in the GAME_GUEST table represents a DC guest in a game. Occasionally in the earlier years more than one guest appeared in one game. Such games would have one entry in this table for each guest.

Definition
CREATE TABLE game_guest (
	ep_id	text not null references game(ep_id),
	p_id	int not null references person(id),
	name	text not null,
	primary key (ep_id, p_id)
);
GAME_LEX
The GAME_LEX table records who was lexicographer for each game.

Definition
CREATE TABLE game_lex (
	ep_id	text not null references game(ep_id),
	p_id	int not null references person(id),
	name	text not null,
	primary key (ep_id, p_id)
);
PLAYER_LETTERS
This table contains one row per player per letters round. It stores information about that letters round which pertains to a particular player, such as what word they offered, whether it was disallowed and why, and how many points they scored.

Other information about the letters round, which is not specific to one of the players, such as the selection and the maximum score available, is recorded in the ROUND_LETTERS table.

Definition
CREATE TABLE player_letters (
	ep_id       text not null references game(ep_id),  -- foreign key into GAME table
	round_no    int not null,                          -- round number in this game
	p_id        int not null references person(id),    -- player; foreign key into PERSON table
	word        text,                                  -- word this player offered (see below)
	adj         int,                                   -- adjudication (see below)
	score       int,                                   -- player's score for this round
	cumul_score int,                                   -- player's score so far in this game, up to and including this round
	primary key(ep_id, round_no, p_id)
);
The word, adj, score and cumul_score fields may be NULL if the information is not known.

The word field contains the word offered by the player. If the player did not offer a declaration, this is blank. If the player declared a length but was not asked for their word because the other player had a longer word (this is unheard of now, but more common in the early years), this field contains a single digit representing the number of letters declared.

The adj field shows how this offering was adjudicated, according to the table below. Note that a negative number indicates a misdeclaration. A misdeclaration is when a contestant offered a word which did not match the declared length, or when a contestant declared a length but then did not offer a word when asked.

adj	Description
0	Accepted
1	Disallowed: unacceptable word
2	Disallowed: not available from selection
3	Disallowed: not written down
-n	Disallowed: length misdeclared as n letters
Sometimes a word is disallowed for more than one reason, but only one reason can be recorded in the table. The order of priority, from highest to lowest, is: not written down; misdeclared; not available from the selection; unacceptable word.

Example
These are the two entries for round 2 of the Series 69 final. Person #5489 is Dylan Taylor and and person #5529 is Callum Todd.

ep_id	round_no	p_id	word	adj	score	cumul_score
5839	2	5470	ENVIOUS	0	0	8
5839	2	5510	SOUVENIR	0	8	8
PLAYER_NUMBERS
Each row in the PLAYER_NUMBERS table represents a player's attempt at a numbers round. There is one row per game per player.

This table stores information about the numbers round which is specific to one of the players, such as their declaration, method, and how many points that player scored. Other information, which is not specific to either player, is stored in the ROUND_NUMBERS and ROUND_NUMBERS_SEL tables.

Definition
CREATE TABLE player_numbers (
	ep_id        text not null references game(ep_id),   -- foreign key into GAME table
	round_no     int not null,                           -- round number in this game
	p_id         int not null references person(id),     -- player ID: foreign key into PERSON table
	dec          int,                                    -- player's declaration or 0 if no declaration
	adj          int,                                    -- adjudication: 0 if accepted, nonzero if not
	method       text,                                   -- player's method, if given
	score        int,                                    -- points scored by player in this round
	cumul_score  int,                                    -- points scored by player so far in this game, up to and including this round
	primary key(ep_id, round_no, p_id)
);

Example
The two entries in PLAYER_NUMBERS for round 9 of this game would look as follows. Person #5568 is Jonathan Liew, who declared 330 and got 7 points, and person #5575 is Tricia Lockhart, who declared 334 but made a mistake.

ep_id	round_no	p_id	dec	adj	method	score	cumul_score
5825	9	5549	330	0	9 × 4 × (5 + 4) + 3 + 3	7	61
5825	9	5556	334	1	☓	0	37
PLAYER_CONUNDRUMS
There is one row in this table for every instance of a player being presented with a conundrum. This means for one conundrum in one game, there are two entries in this table: one for each player. The entry records whether the player buzzed, and if so, the buzz time, their answer, and any points scored.

Other information about the conundrum round which does not correspond specifically to one of the players is stored in the ROUND_CONUNDRUMS table.

Definition
CREATE TABLE player_conundrums (
	ep_id       text not null references game(ep_id), -- foreign key to GAME table
	round_no    int not null,                         -- round number within this game
	p_id        int not null references person(id),   -- foreign key to PERSON table
	buzz        int,                                  -- 1 if contestant buzzed, 0 otherwise
	buzz_time   real,                                 -- time of buzz
	answer      text,                                 -- contestant's answer
	score       int,                                  -- contestant's score for this round
	cumul_score int,                                  -- contestant's cumulative score so far in the game, up to and including this round
	primary key(ep_id, round_no, p_id)
);
Examples
The entries in PLAYER_CONUNDRUMS for the conundrum for the 30th Birthday Championship final are as follows.

ep_id	round_no	p_id	buzz	buzz_time	answer	score	cumul_score
5654	15	3733	1	0.75	LEVIATHAN	10	146
5654	15	4889	0	NULL	NULL	0	111
The entries for the 30th Birthday Championship game between Kirk Bevins and Innis Carson are as follows.

ep_id	round_no	p_id	buzz	buzz_time	answer	score	cumul_score
5645	15	3387	1	2.5	CERVULINE	0	102
5645	15	4591	1	18.0	CURVELINE	0	102
5645	16	3387	1	1.5	BRICKYARD	10	112
5645	16	4591	0	NULL	NULL	0	102
ROUND_LETTERS
The ROUND_LETTERS table contains one row for every letters round. It stores the selection and maximum score available in that round. Information about the players' offerings in the round can be round in the PLAYER_LETTERS table.

Definition
CREATE TABLE round_letters (
	ep_id           text not null references game(ep_id),  -- episode ID: foreign key into GAME table
	round_no        int not null,                          -- round number in this game
	selection       text,                                  -- letters selection for this round
	max_score       int,                                   -- maximum score available from this round
	max_cumul_score int,                                   -- maximum score available so far in this game, up to and including this round
	primary key(ep_id, round_no)
);
Note that for games earlier than the introduction of the ODE2r, the max_score field, and hence the max_cumul_score field, may not be correct.

ROUND_NUMBERS
Each row in the ROUND_NUMBERS table represents a numbers round. It stores the arithmetician's effort, if given, and the closest declaration possible.

Information relating to the players' declarations and methods can be found in the PLAYER_NUMBERS table. The selection for each numbers round is stored in the ROUND_NUMBERS_SEL table.

Definition
CREATE TABLE round_numbers (
	ep_id           text not null references game(ep_id),   -- episode ID: foreign key into GAME table
	round_no        int not null,                           -- round number in this game
	target          int,                                    -- target for this round
	arith_dec       int,                                    -- arithmetician's declaration, if known
	arith_method    text,                                   -- arithmetician's method, if known
	best_dec        int,                                    -- a closest possible declaration
	best_method     text,                                   -- a method for achieving best_dec
	max_score       int,                                    -- maximum number of points available from this round
	max_cumul_score int,                                    -- maximum number of points available so far in this game, up to and including this round
	primary key(ep_id, round_no)
);

Example
This is the row in ROUND_NUMBERS for round 9 of episode 5825, which is the same round as in the PLAYER_NUMBERS example above. Note that Rachel's effort is not known for this round.

ep_id	round_no	target	arith_dec	arith_method	best_dec	best_method	max_score	max_cumul_score
5825	9	332	NULL	NULL	332	((9 + 4 + 3) × 5 + 3) × 4	10	76
ROUND_NUMBERS_SEL
There is one row in this table for each of the six numbers drawn in one numbers round of one game. The numbers selection is placed in a separate table to enable easier identification of how many large numbers in a round, how many times the 100 has been drawn, etc.

Definition
CREATE TABLE round_numbers_sel (
	ep_id    text not null references game(ep_id),  -- episode ID: foreign key into GAME game
	round_no int,                                   -- round number in this game
	seq      int not null,                          -- sequence number between 0 and 5 for this number - 0 is the leftmost number, 5 the rightmost
	num      int,                                   -- the number
	primary key(ep_id, round_no, seq)
);
Example
The row in ROUND_NUMBERS_SEL for round 9 of episode 5825, which is the same round as used in the example before, looks like this.

ep_id	round_no	seq	num
5825	9	0	4
5825	9	1	3
5825	9	2	3
5825	9	3	4
5825	9	4	9
5825	9	5	5
ROUND_CONUNDRUMS
Each row in this table represents a conundrum round, and stores information such as the scramble, whether it was a tiebreak, and what the solution was. Information specific to one of the players, such as buzz times and scores, is stored in the PLAYER_CONUNDRUMS table.

Definition
CREATE TABLE round_conundrums (
	ep_id           text not null references game(ep_id), -- episode ID: foreign key into GAME table
	round_no        int not null,                         -- round number in this game
	tiebreak        int,                                  -- 1 if this was a tiebreak, 0 if not
	selection       text,                                 -- the conundrum scramble
	order_known     int,                                  -- 1 if the order of the letters in the selection field is known to be correct, 0 if not
	answer          text,                                 -- the correct answer
	max_score       int,                                  -- the maximum score available in this round (always 10)
	max_cumul_score int,                                  -- the maximum score available in the game so far, up to and including this round
	primary key(ep_id, round_no)
);
For some early games, we know the conundrum solution but not the order of the letters in the scramble shown to the players. In those cases, the letters in the selection field are in an arbitrary order (specified by the wiki, and probably always alphabetical order) and the order_known field is 0.

It is unspecified whether tiebreak rounds count towards max_cumul_score. Because the database was generated from the wiki, in each individual game the value of max_cumul_score will reflect what the wiki said, and there might not be a consistent policy. It's probably best not to rely on the exact value of max_cumul_score for tiebreak rounds.

Example
The row in ROUND_CONUNDRUMS for the Series 69 final, episode 5839, looks as follows.

ep_id	round_no	tiebreak	selection	order_known	answer	max_score	max_cumul_score
5839	15	0	IHURTPALM	1	TRIUMPHAL	10	134
Views
ROUND_PLAYER_UNION
The ROUND_PLAYER_UNION table combines selected columns from PLAYER_LETTERS, PLAYER_NUMBERS and PLAYER_CONUNDRUMS into one view. Only columns that have meaning for all three round types appear: they are the episode ID and round number, round type, player ID, the player's score for this round, and the player's cumulative score so far.

Note the round_type column is L, N or C for a letters round, numbers round or conundrum round respectively.

Definition
CREATE VIEW round_player_union as
        select ep_id, round_no, 'L' round_type, p_id, score, cumul_score from player_letters
        union
        select ep_id, round_no, 'N' round_type, p_id, score, cumul_score from player_numbers
        union
        select ep_id, round_no, 'C' round_type, p_id, score, cumul_score from player_conundrums;
Example
The entries in ROUND_PLAYER_UNION representing Michael Goldman's offerings in Episode 1 are as follows.

ep_id	round_no	round_type	p_id	score	cumul_score
1	1	L	1	7	7
1	2	L	1	6	13
1	3	L	1	5	18
1	4	N	1	0	18
1	5	L	1	7	25
1	6	L	1	5	30
1	7	L	1	5	35
1	8	N	1	5	40
1	9	C	1	10	50
The query that produced the above results was:

select rpu.*
from round_player_union rpu, person p
where rpu.p_id = p.id
and ep_id = '1'
and p.name = 'Michael Goldman'
order by rpu.round_no;
ROUND_UNION
The ROUND_UNION view combines selected columns from ROUND_LETTERS, ROUND_NUMBERS and ROUND_CONUNDRUMS. It contains only those columns which appear in all those three tables.

Definition
CREATE VIEW round_union as
        select ep_id, round_no, 'L' round_type, max_score, max_cumul_score from round_letters
        union
        select ep_id, round_no, 'N' round_type, max_score, max_cumul_score from round_numbers
        union
        select ep_id, round_no, 'C' round_type, max_score, max_cumul_score from round_conundrums;
Example
These are the rows in ROUND_UNION for all the rounds of Episode 1.

ep_id	round_no	round_type	max_score	max_cumul_score
1	1	L	7	7
1	2	L	7	14
1	3	L	5	19
1	4	N	10	29
1	5	L	7	36
1	6	L	5	41
1	7	L	6	47
1	8	N	10	57
1	9	C	10	67
Example queries
The following example SQL queries illustrate how to use the tables in the database. Note that the results you see here may be out of date by the time you read them. They are correct as of the end of Series 87.

Most common numbers targets
For all broadcast episodes, find the ten most common numbers round targets.

Query
select rn.target, count(*)
from round_numbers rn, game g
where rn.ep_id = g.ep_id
and g.tx_date is not null
and rn.target is not null
group by rn.target
order by 2 desc
limit 10;
Results
target	count(*)
609	49
942	43
670	43
910	42
727	42
270	41
237	41
874	40
561	40
314	40
Guests and lexicographers who have also appeared as contestants
Find the names of everyone who has appeared on the show as a contestant, and has also appeared as a lexicographer or dictionary corner guest. Special episodes 495 and 2874 accounts for some of the results here.

Query
select p.name
from person p, game_player gp, game g
on g.ep_id = gp.ep_id and gp.p_id = p.id
where (
	p.id in (select p_id from game_guest)
	or p.id in (select p_id from game_lex)
)
and g.tx_date is not null
group by p.id;
Results
name
Michael Wylie
Gyles Brandreth
Mark Nyman
Bill Tidy
Damian Eadie
Jo Brand
Matt Le Tissier
Carol King
Highest scores
For selected episode formats, list the highest score achieved in that format, the player who achieved it, and the episode number and date on which it occurred. Order the results by score with the highest first.

Query
select f.name format, gp.name, gp.score, g.ep_id, g.tx_date
from format f, game g, game_player gp,
	(select g1.format, max(gp1.score) record from game_player gp1, game g1
	where gp1.ep_id = g1.ep_id
	group by g1.format) formatrecords
where f.id = g.format
and g.ep_id = gp.ep_id
and g.format = formatrecords.format
and gp.score = formatrecords.record
and f.name in ('15 rounder', 'Old 15 rounder', 'Masters', '14 rounder', '9 rounder')
order by 3 desc;
Results
format	name	score	ep_id	tx_date
15 rounder	Tom Stevenson	154	7860	2022-09-29
15 rounder	Cillian McMulkin	154	7943	2023-01-31
Old 15 rounder	Julian Fell	146	3387	2002-12-18
Old 15 rounder	Conor Travers	146	5654	2013-03-01
Masters	Julian Hough	124	M16	1989-07-17
14 rounder	Harvey Freeman	115	601	1987-06-30
9 rounder	Allan Saldanha	83	1886	1996-11-21
9 rounder	Stephen Balment	83	546	1987-04-14
Biggest comebacks
Find the ten games with the highest overturned deficits. Give the episode ID, broadcast date, contestant names and scores of each match, as well as the largest lead the eventual loser had over the eventual winner.

Query
select g.ep_id, g.tx_date,
	gpwinner.name winner_name, gpwinner.score winner_score,
	gploser.name loser_name, gploser.score loser_score,
	max(rpuloser.cumul_score - rpuwinner.cumul_score) deficit
from game g, game_player gpwinner, game_player gploser,
	round_player_union rpuwinner, round_player_union rpuloser
where g.ep_id = gpwinner.ep_id
and g.ep_id = gploser.ep_id
and gpwinner.score > gploser.score
and g.ep_id = rpuwinner.ep_id
and gpwinner.p_id = rpuwinner.p_id
and gploser.p_id = rpuloser.p_id
and rpuwinner.ep_id = rpuloser.ep_id
and rpuwinner.round_no = rpuloser.round_no
group by 1,2,3,4,5,6
order by 7 desc limit 10;
Results
ep_id	tx_date	winner_name	winner_score	loser_name	loser_score	deficit
3645	2004-02-16	Richard Pay	79	Claire Whitaker	77	40
5896	2014-03-31	Ann Robinson	73	Trevor Grundy	67	39
8042	2023-06-19	Sarah Bibby	82	Tony McCooey	79	39
444	1986-06-03	David Trace	80	Mick Keeble	74	35
5738	2013-07-23	Rory Coleman	81	Graham Harrison	79	33
4865	2009-07-21	Paul Varlaam	72	Yvonne Battelle	71	30
3863	2005-02-03	Nicky Lyons	85	Sonia Cordas	79	28
4103	2006-05-15	Tony Warren	71	Michael Gordon	64	28
4141	2006-07-06	Phil Watson	63	Paul Collings	52	28
7291	2020-03-25	Mike Nevins	72	George Beach	67	28

"""

# --- 3. THE LLM FUNCTION ---
def translate_text_to_sql(user_question):
    """Sends the schema and user question to Gemini to get SQL and assumptions."""
    
    prompt = f"""
    You are an expert SQLite developer and Countdown show historian. 
    Translate the user's question into a valid, read-only SQL query.
    
    CRITICAL RULES:
    1. You MUST respond with a valid JSON object.
    2. Do NOT wrap the JSON in markdown blocks (no ```json).
    3. The JSON must exactly match the structure below.
    
    JSON STRUCTURE:
    {{
        "sql_query": "The raw SQL query string here",
        "assumptions": [
            "Any assumption you made about what the user meant.",
            "Any clarification about edge cases (e.g., 'Excluding tiebreaks').",
            "If the question was perfectly clear, write 'No major assumptions made.'"
        ]
    }}

    TERMINOLOGY:
    {TERMINOLOGY}
    
    DATABASE SCHEMA AND ACCOMPANYING NOTES:
    {SCHEMA_TEXT}
    
    USER QUESTION: 
    {user_question}
    """
    
    # We enforce JSON output using the config
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
        )
    )
    
    # Parse the JSON string into a Python dictionary
    try:
        result_dict = json.loads(response.text)
        return result_dict.get("sql_query", ""), result_dict.get("assumptions", [])
    except json.JSONDecodeError:
        raise ValueError("The LLM failed to return valid JSON.")

# --- 4. THE STREAMLIT UI ---
st.title("🔢 Countdown TV Show Explorer")
st.markdown("Ask a question about historical Countdown episodes, contestants, and scores in plain English.")

user_question = st.text_input("Example: Who had the highest score in series 50?")

if user_question:
    with st.spinner("Analyzing question and writing SQL..."):
        try:
            # 1. Get the SQL and Assumptions from Gemini
            generated_sql, assumptions = translate_text_to_sql(user_question)
            
            # 2. Display the Assumptions
            st.write("### AI Agent Assumptions")
            if assumptions:
                for assumption in assumptions:
                    st.markdown(f"* {assumption}")
            else:
                st.write("* No major assumptions made.")
                
            st.divider() # Visual separator
            
            # 3. Display the SQL
            st.write("### Generated SQL Query")
            st.code(generated_sql, language="sql")
            
            # 4. Connect to the database safely
            db_uri = 'file:countdown (8).db?mode=ro'
            conn = sqlite3.connect(db_uri, uri=True)
            
            # 5. Execute the query
            results_df = pd.read_sql_query(generated_sql, conn)
            conn.close()
            
            # 6. Display the results
            st.write("### Query Results")
            if results_df.empty:
                st.info("The query ran successfully, but returned no results.")
            else:
                st.dataframe(results_df, use_container_width=True)
                
        except sqlite3.Error as e:
            st.error(f"**Database Error:** The generated SQL was invalid. \n\nDetails: {e}")
        except Exception as e:
            st.error(f"**Application Error:** {e}")
