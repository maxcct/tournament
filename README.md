# tournament
Simulates ‘Swiss-system’ tournaments and stores the results in a database

## TOURNAMENT SIMULATOR SET-UP                        
1. Go to [udacity.atlassian.net/wiki/display/BENDH/Vagrant+VM+Installation](udacity.atlassian.net/wiki/display/BENDH/Vagrant+VM+Installation)

2. Follow the instructions for setting up Git (if applicable), VirtualBox and Vagrant

3. Follow the instructions for forking the GitHub repository

4. Follow the instructions for getting Vagrant up and logging into it

5. Once you're logged in, enter `cd /vagrant/tournament`

6. Enter `psql`, then `\i tournament.sql`. You should see 'CREATE DATABASE', then
   'CREATE TABLE' x 3, 'CREATE VIEW' x 4

7. Enter `\q`, then `python tournament.py`. Messages stating who won each simulated
   tournament should appear

8. To view details of the simulated tournaments, enter `psql tournament`, then enter
   an appropriate SQL query. The most useful tables for overviews of the data can be
   accessed by entering the following queries:
```
        SELECT * FROM ordered_matches;
        SELECT * FROM ranked_players;
```
The details of the tournaments simulated can be changed by making minor alterations to the
code in the file 'tournament.py'. The program includes six lists of varying numbers of entrants
by default, but any number of names and any form of name (as long as they're all strings) can
be used. Just modify the lists located at the top of the file, or add a new list or lists then
modify the arguments of the `initiateTournament` function calls (see below) accordingly.

The file has seven function calls at the bottom: first, a call to wipe the database of any
existing records. Then the `initiateTournament` function is called six times with different lists
of entrants as arguments. This simulates six successive, separate tournaments and populates the
database accordingly.

The user may add or subtract from the number of `initiateTournament` calls to determine how many
tournaments will be simulated. They may also remove or comment-out the 'wipeDatebase' call if they
wish to maintain the records of prior tournaments when simulating new tournaments.

Here follow some details of the program's tournament simulations:

Odd and even numbers of entrants may participate. If the number of entrants is odd, one of them
will be randomly chosen to be given a 'bye' in the first round; in subsequent rounds, the 'bye' is
given to the lowest-ranked player who has not already received a 'bye' in the current tournament.
A 'bye' means that the player is given a free win, and blank opponent details are entered into the
records for that match.

In the first round, players are paired at random. Subsequent rounds use the Swiss system: the
highest-ranked player plays the next-highest ranked, and so on. When players are equally ranked by
wins, they are sub-ranked according to the sum of their opponents' wins. This means that if two
players each have three wins, but the opponents that player A has already played have five wins
between them while the opponents of player B have four, then player A will be ranked above player B
for the purposes of Swiss pairing and assigning byes (and for deciding tournament victory).
