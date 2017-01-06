DROP DATABASE IF EXISTS tournament;
-- Any existing tournament database will be dropped once this SQL filed is imported.

CREATE DATABASE tournament;

\c tournament

CREATE TABLE players (id serial PRIMARY KEY,
	                  name text,
	                  tournament_id integer);

CREATE TABLE matches (round integer,
	                  winner_id integer REFERENCES players(id),
	                  loser_id integer,
	                  tournament_id integer REFERENCES players,
	                  pairing_id serial PRIMARY KEY);

CREATE TABLE byes (byed_player_id integer UNIQUE PRIMARY KEY,
	               tournament_id integer REFERENCES players);
-- Records players who have received a 'bye', so that they can be excluded from
-- further 'byes' in the same tournament.

CREATE VIEW ordered_matches AS SELECT * FROM matches ORDER BY tournament_id, round;
-- See records of all matches played, ordered by tournament and then by round.

CREATE VIEW wins AS SELECT players.id,
                           players.name,
                           count(matches.winner_id) as wins,
                           count(matches.loser_id) as losses,
                           players.tournament_id
                           FROM players LEFT OUTER JOIN matches
                           ON players.tournament_id = matches.tournament_id
                           AND players.id = matches.winner_id
                           GROUP BY matches.tournament_id, players.id
                           ORDER BY players.tournament_id, wins DESC;


CREATE VIEW defeats AS SELECT players.id,
                              count(matches.loser_id) as losses,
                              players.tournament_id
                              FROM players LEFT OUTER JOIN matches
                              ON players.tournament_id = matches.tournament_id
                              AND players.id = matches.loser_id
                              GROUP BY matches.tournament_id, players.id
                              ORDER BY players.tournament_id, losses;
-- See records of each player's defeats, ordered by tournament and then by round.

CREATE VIEW win_rankings AS SELECT wins.id,
                                   wins.name,
                                   wins.wins,
                                   defeats.losses,
                                   wins.tournament_id
                                   FROM wins JOIN defeats
                                   ON wins.id = defeats.id
                                   ORDER BY wins.tournament_id, wins DESC;
-- See records of each player's victories and defeats, ordered by tournament and then by round.

-- Please see note below on the following eight queries.
CREATE VIEW opp1 AS SELECT players.id,
                           matches.loser_id,
                           players.tournament_id
                           FROM players LEFT OUTER JOIN matches
                           ON players.id = matches.winner_id
                           WHERE matches.loser_id != 0
                           AND players.tournament_id = matches.tournament_id
                           ORDER BY players.id;

CREATE VIEW opp2 AS SELECT players.id,
                           matches.winner_id,
                           players.tournament_id
                           FROM players LEFT OUTER JOIN matches
                           ON players.id = matches.loser_id
                           AND players.tournament_id = matches.tournament_id
                           ORDER BY players.id;

CREATE VIEW x AS SELECT opp1.id,
                        (SELECT wins FROM wins WHERE id = opp1.loser_id) as wins2,
                        opp1.tournament_id
                        FROM opp1 LEFT OUTER JOIN wins
                        ON opp1.loser_id = wins.id
                        AND opp1.tournament_id = wins.tournament_id
                        GROUP BY opp1.tournament_id, opp1.id, opp1.loser_id;

CREATE VIEW y AS SELECT opp2.id,
                        (SELECT wins FROM wins WHERE id = opp2.winner_id) as wins1,
                        opp2.tournament_id
                        FROM opp2 LEFT OUTER JOIN wins
                        ON opp2.winner_id = wins.id
                        AND opp2.tournament_id = wins.tournament_id
                        GROUP BY opp2.tournament_id, opp2.id, opp2.winner_id;

CREATE VIEW a AS SELECT players.id,
                        y.wins1, players.tournament_id
                        FROM players LEFT OUTER JOIN y
                        ON players.id = y.id
                        AND players.tournament_id = y.tournament_id
                        GROUP BY players.tournament_id, players.id, y.wins1
                        ORDER BY players.id;

CREATE VIEW b AS SELECT players.id,
                        x.wins2,
                        players.tournament_id
                        FROM players LEFT OUTER JOIN x
                        ON players.id = x.id
                        AND players.tournament_id = x.tournament_id
                        GROUP BY players.tournament_id, players.id, x.wins2
                        ORDER BY players.id;

CREATE VIEW c AS SELECT id,
                        sum(wins1),
                        a.tournament_id
                        FROM a
                        GROUP BY a.tournament_id, id
                        ORDER BY id;

CREATE VIEW d AS SELECT id,
                        sum(wins2),
                        b.tournament_id
                        FROM b
                        GROUP BY b.tournament_id, id
                        ORDER BY id;

-- Note on the above eight queries: knowing no more SQL than was taught in the final few lessons
-- of this course and what I could pick up from Google, I required all this code to calculate
-- 'opponent match wins' for each player. I realise there must surely be a more economical way
-- to achieve the same end, but I spent an entire day on this, and I think it's about the best I
-- can reasonably be expected to accomplish at this stage in my education.


CREATE VIEW opp_match_wins AS SELECT c.id as player_id,
                                     coalesce(c.sum, d.sum) as opponent_wins,
                                     c.tournament_id
                                     FROM c JOIN d
                                     ON c.id = d.id
                                     AND c.tournament_id = d.tournament_id
                                     GROUP BY c.tournament_id, player_id, opponent_wins
                                     ORDER BY player_id;
-- See the total number of victories obtained by all a given player's previous opponents.

CREATE VIEW victories AS SELECT wins.id,
                                wins.name,
                                wins.wins,
                                wins.losses,
                                opp_match_wins.opponent_wins,
                                wins.tournament_id
                                FROM wins JOIN opp_match_wins
                                ON wins.id = opp_match_wins.player_id
                                AND wins.tournament_id = opp_match_wins.tournament_id
                                ORDER BY wins.tournament_id, wins.wins DESC,
                                opp_match_wins.opponent_wins DESC;
-- See records of each player's victories, ordered by wins and then by 'opponent match wins'.

CREATE VIEW rankings AS SELECT victories.id,
                               victories.name,
                               victories.wins,
                               defeats.losses,
                               victories.opponent_wins,
                               victories.tournament_id
                               FROM victories JOIN defeats
                               ON victories.id = defeats.id
                               AND victories.tournament_id = defeats.tournament_id
                               ORDER BY victories.tournament_id, wins DESC,
                               victories.opponent_wins DESC;
-- See records of each player's victories, defeats and 'opponent match wins',
-- ordered by wins and then by 'opponent match wins'.