#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2
import math
import random
import copy


entrants1 = ['Max', 'Emma', 'Harry', 'Quentin', 'Jemima', 'Joe',
             'Eliza', 'Anne', 'Zoe', 'Mark', 'Alex', 'Lucy',
             'Charlotte', 'Jessica', 'Luke', 'Eve', 'Jerry']

entrants2 = ['Bobthwaite', 'Arnold', 'Solange', 'Beyonce']

entrants3 = ['Johan', 'Ned', 'Bubba', 'Hanna', 'Beelzebub']

entrants4 = ['Lara', 'Ted', 'Jonas', 'Griffin', 'Lila', 'Yolanda']

entrants5 = ['Max', 'Emma', 'Harry', 'Quentin', 'Jemima', 'Joe',
             'Eliza', 'Anne', 'Zoe', 'Mark', 'Alex', 'Lucy',
             'Charlotte', 'Jessica', 'Luke', 'Eve']


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def initiateTournament(entrants):
    """Initiates a new tournament. If previously played tournaments are in the
    database, assigns the new tournament the next tourmanent id. If there are
    none, wipes the database in case it contains any unwanted records.
    Args:
      entrants: a list of entrants' names (full, first, or whatever, as long
      as it's a string). (Need not be unique.)
    """
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT max(tournament_id) FROM matches;")
    prior_tournament = c.fetchone()[0]
    if prior_tournament is not None:
        tournament_id = prior_tournament + 1
        conn.close()
        total_rounds = calculateTotalRounds(entrants, tournament_id)
    else:
        wipeDatabase()
        tournament_id = 1  # Because it's the first tournament
        total_rounds = calculateTotalRounds(entrants, tournament_id)
    conn.close()
    randomFirstRoundPairings(total_rounds, tournament_id)


def calculateTotalRounds(entrants, tournament_id):
    """Calculates a number of rounds appropriate to the number of players.

    Args:
      tournament_id: identifier of the tournament the players are being
      enrolled in. (I won't annotate further uses of this argument, as it's
      used by most of the functions.)
    """
    registerPlayers(entrants, tournament_id)
    num_of_players = countPlayers(tournament_id)
    if num_of_players > 4:
        total_rounds = int(math.log(num_of_players, 2))
    else:
        total_rounds = 1
    return total_rounds


def wipeDatabase():
    deleteMatches()
    deletePlayers()


def deleteMatches():
    """Remove all the match and results records from the database."""
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM matches;")
    c.execute("ALTER SEQUENCE matches_pairing_id_seq RESTART WITH 1;")
    c.execute("UPDATE matches SET pairing_id = DEFAULT;")
    conn.commit()
    conn.close()


def deletePlayers():
    """Remove all the player records from the database."""
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM byes;")
    c.execute("DELETE FROM players;")
    c.execute("ALTER SEQUENCE players_id_seq RESTART WITH 1;")
    c.execute("UPDATE players SET id = DEFAULT;")
    conn.commit()
    conn.close()


def countPlayers(tournament_id):
    """Counts the players participating in the current tournament."""
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT count(*) as num FROM players "
              "WHERE tournament_id = (%s);", (tournament_id,))
    player_count = c.fetchone()[0]
    conn.close()
    return player_count


def registerPlayers(entrants, tournament_id):
    """Adds entrants into the tournament database in a randomised order.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      entrants: a list of entrants' names.
    """
    conn = connect()
    c = conn.cursor()
    enrolment = copy.copy(entrants)
    while enrolment != []:
        name = random.choice(enrolment)
        c.execute("INSERT INTO players VALUES (DEFAULT, (%s), (%s));",
                  (name, tournament_id))
        enrolment.remove(name)
    conn.commit()
    conn.close()


def playerStandings(tournament_id, bye=None):
    """Returns a list of the players and their personal match stats for the
    current tournament (as defined by the first argument), sorted first by
    wins and then by the sum of their opponents' wins.

    The first entry in the list should be the player with the most wins, or,
    if there is currently a tie, the player with the joint-most wins whose
    previous opponents have had the most wins in total.

    Returns:
      A list of tuples, each of which contains the players' id, name, wins,
      opponent wins and matches played, in that order:
        id: the player's unique id (assigned by the database)
        name: the player's name (as registered)
        wins: the number of matches the player has won
        opponent_wins: the total number of wins obtained by all the player's
        previous opponents
        matches: the number of matches the player has played
    Args:
      bye: indicates that one of the players has been given an automatic win,
      because there are an odd number of participants. It is set to 'None' by
      default, but if a player id is passed in, this function will return the
      list of players minus the player receiving the 'bye'. This allows that
      player to be dealt with separately from those who will be competing with
      each other.
    """
    conn = connect()
    c = conn.cursor()
    if bye:
        c.execute("SELECT id, name, wins, opponent_wins "
                  "FROM rankings WHERE tournament_id = (%s) "
                  "AND id != (%s);", (tournament_id, bye))
    else:
        c.execute("SELECT id, name, wins, opponent_wins FROM rankings "
                  "WHERE tournament_id = (%s);", (tournament_id,))
    player_standings = c.fetchall()
    conn.close()
    return player_standings


def determineWinners(pairings, total_rounds, tournament_id):
    """Simulates the playing of a match for each pair of players, and updates
    the relevant tallies for each round played. Randint is used to determine
    which of the two players (distinguished as 'red' and 'blue') wins.
    Excludes players who have received a 'bye', as they are assigned a win
    automatically and have no opponent.

    Args:
      total_rounds: allows the function to track whether the final round has
      been played, at which point mySwissPairings will not be called (as it
      otherwise is) after the current round has been resolved, so another
      round will not be initiated.
    """
    this_round = thisRound(tournament_id)
    conn = connect()
    c = conn.cursor()
    count = 0
    num_of_players = len(pairings)
    if num_of_players < 4:
        stopping_point = 1
    elif num_of_players == 4:
        stopping_point = 2
    else:
        stopping_point = num_of_players - 2
    while count < stopping_point:
        for pair in pairings:
            if count % 2 == 0:
                count += 1
                victor = random.randint(0, 1)
                if victor == 0:
                    c.execute("INSERT INTO matches "
                              "VALUES ((%s), (%s), (%s), (%s));",
                              (this_round, pair, pairings[count],
                               tournament_id))
                elif victor == 1:
                    c.execute("INSERT INTO matches "
                              "VALUES ((%s), (%s), (%s), (%s));",
                              (this_round, pairings[count], pair,
                               tournament_id))
            else:
                count += 1
    conn.commit()
    conn.close()
    if this_round < total_rounds:
        mySwissPairings(total_rounds, tournament_id)
    else:
        printVictory(tournament_id)


def printVictory(tournament_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT name, id FROM rankings "
              "WHERE tournament_id = (%s);", (tournament_id,))
    rankings = c.fetchall()
    victor = rankings[0][0]
    victor_id = str(rankings[0][1])
    conn.close()
    print ('\n' + victor + ' (ID:' + victor_id + ') ' +
           'was victorious in tournament ' + str(tournament_id) + '!\n')


def thisRound(tournament_id):
    """Ascertains the current round number."""
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT max(round) FROM matches WHERE tournament_id = (%s) "
              "AND loser_id != (%s);", (tournament_id, 0))
    last_round = c.fetchone()[0]
    if last_round is None:
        this_round = 1
    else:
        this_round = last_round + 1
    conn.close()
    return this_round


def obtainPlayerIDs(tournament_id):
    """Obtains list of player IDs from players table. This allows first-round
    random pairings to be made for any number of competitors.

    Returns:
      A list of ids of the players participating in the current tournament.
    """
    player_ids = []
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM players WHERE tournament_id = (%s);",
              (tournament_id,))
    num_of_players = c.fetchone()[0]
    c.execute("SELECT max(id) FROM players;")
    highest_player_id = c.fetchone()[0]
    lowest_player_id = highest_player_id - num_of_players
    conn.close()
    for n in range(lowest_player_id+1, highest_player_id+1):
        player_ids.append(n)
    return player_ids


def nameFromID(player_id, tournament_id):
    """Obtains (and returns) player name from player ID (first arg)."""
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT name FROM players WHERE id = (%s) "
              "AND tournament_id = (%s);", (player_id, tournament_id))
    name = c.fetchone()[0]
    conn.close()
    return name


def opponentWins(player_id, tournament_id):
    """Calculates the sum of the matches won by a player's previous opponents.

    Args:
      player_id: id of the player whose opponents' wins are being summed.
    """
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT loser_id FROM matches WHERE winner_id = (%s) "
              "AND tournament_id = (%s);", (player_id, tournament_id))
    blue_opponents = c.fetchall()
    c.execute("SELECT winner_id FROM matches WHERE loser_id = (%s) "
              "AND tournament_id = (%s);", (player_id, tournament_id))
    red_opponents = c.fetchall()
    opponents = blue_opponents + red_opponents
    total_opponent_wins = 0
    for opponent in opponents:
        c.execute("SELECT wins FROM rankings WHERE id = (%s) "
                  "AND tournament_id = (%s);", (opponent[0], tournament_id))
        opponent_wins = c.fetchone()
        if opponent_wins is not None:
            total_opponent_wins += opponent_wins[0]
    c.execute("UPDATE players SET opponent_wins = (%s) WHERE id = (%s) "
              "AND tournament_id = (%s);",
              (total_opponent_wins, player_id, tournament_id))
    conn.commit()
    conn.close()


def randomPairingsForEvenNumbers(player_ids):
    """Randomly pairs up players for the next round and populates the
    'matches' table accordingly. This function is called immediately by
    randomFirstRoundPairings when the number of entrants is even, or is
    called after a 'byed' player has been removed from contention if the
    number of entrants is odd.

    Args:
      this_round: the current round (I won't annotate this one again).
      player_ids: ids of the players to be randomly paired.
    """
    pairings = []
    while player_ids != []:
        red_player_id = random.choice(player_ids)
        player_ids.remove(red_player_id)
        pairings.append(red_player_id)
        blue_player_id = random.choice(player_ids)
        player_ids.remove(blue_player_id)
        pairings.append(blue_player_id)
    return pairings


def givePlayerABye(this_round, bye_id, tournament_id):
    """If there is an odd number of entrants, this function allows a surplus
    player to be given a 'bye': a free win. The various tables are updated
    accordingly, and the player's id is entered into the 'byes' table so that
    then can be prevented from receiving more than one bye in the same
    tournament. The byed player is chosen at random in the first round; in
    subsequent rounds it is the lowest-ranked player who has not already
    received a bye.

    Args:
      bye_id: id of the player receiving the bye.
    """
    bye_name = nameFromID(bye_id, tournament_id)
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO matches VALUES ((%s), (%s), (%s), (%s));",
              (this_round, bye_id, 0, tournament_id))
    c.execute("INSERT INTO byes VALUES ((%s), (%s));",
              (bye_id, tournament_id))
    conn.commit()
    conn.close()


def randomFirstRoundPairings(total_rounds, tournament_id):
    """If the number of entrants is even, calls randomPairingsForEvenNumbers.
    If it is odd, calls givePlayerABye then randomPairingsForEvenNumbers.
    Finally, calls determineWinners to settle results of the matches between
    the players paired up.

    Args:
      total_rounds: see determineWinners docstring.
      As it's used often, I won't annotate this arg again.
    """
    this_round = 1
    player_ids = obtainPlayerIDs(tournament_id)
    if len(player_ids) % 2 == 0:
        pairings = randomPairingsForEvenNumbers(player_ids)
    else:
        bye_id = random.choice(player_ids)
        givePlayerABye(this_round, bye_id, tournament_id)
        player_ids.remove(bye_id)
        pairings = randomPairingsForEvenNumbers(player_ids)
    determineWinners(pairings, total_rounds, tournament_id)


def mySwissPairingsForEvenNumbers(player_list):
    """Pairs up players for the next round and populates the 'matches' table
    accordingly, using the Swiss system. The player_list is ordered by most
    wins, then by most opponent wins. The first player -- and therefore the
    highest rank -- in the list is paired with the second -- and thus the
    second-highest ranked -- and so on. This function is called immediately by
    mySwissPairings when the number of entrants is even, or after a 'byed'
    player has been removed from contention if the number of entrants is odd.

    Args:
      player_list: a list of details of all players participating in the
      current tournament, sorted by wins (desc) then opponent wins (desc).
    """
    count = 0
    pairings = []
    for row in player_list:
        count += 1
        if count % 2 != 0:
            red_player_id = row[0]
            pairings.append(red_player_id)
        else:
            blue_player_id = row[0]
            pairings.append(blue_player_id)
    return pairings


def mySwissPairings(total_rounds, tournament_id):
    """This function brings together many of the others (I realise it's a
    little long, but most of that length is just storing variables and
    calling other functions). It begins by updating the opponent_wins column
    for each player, allowing them to be ranked properly for Swiss pairing.
    If the number of players is even, mySwissPairingsForEvenNumbers is called.
    If it is odd, the lowest-ranked player is checked to see if they have
    already received a bye in the current tournament. If they have, the
    next-lowest-ranked player is selected, and so on until a player has been
    given a bye. The remaining players are then passed on to
    mySwissPairingsForEvenNumbers. Finally, determineWinners is called to
    settle the outcomes of the matches made.
    """
    conn = connect()
    c = conn.cursor()
    player_ids = obtainPlayerIDs(tournament_id)
    this_round = thisRound(tournament_id)
    num_of_players = countPlayers(tournament_id)
    player_list = playerStandings(tournament_id, None)
    if num_of_players % 2 == 0:
        pairings = mySwissPairingsForEvenNumbers(player_list)
    else:
        c.execute("SELECT byed_player_id FROM byes "
                  "WHERE tournament_id = (%s);", (tournament_id,))
        byed_players = c.fetchall()
        for row in byed_players:
            if row[0] in player_ids:
                player_ids.remove(row[0])
        bye_id = player_ids[-1]
        givePlayerABye(this_round, bye_id, tournament_id)
        player_list = playerStandings(tournament_id, bye_id)
        pairings = mySwissPairingsForEvenNumbers(player_list)
    conn.close()
    determineWinners(pairings, total_rounds, tournament_id)


wipeDatabase()
initiateTournament(entrants1)
initiateTournament(entrants2)
initiateTournament(entrants3)
initiateTournament(entrants4)
initiateTournament(entrants5)
