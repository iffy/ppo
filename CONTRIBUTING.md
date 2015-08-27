If you'd like `ppo` to be able to parse the output of a program:

# Short version #

1. Clone this repo:

    git clone git@github.com:iffy/ppo.git

2. Create a branch

    git branch mybranch

3. Add some example output from the program in the format `functests/cases/in-<programname>-<desc>`:

    nmap -sP > functests/cases/in-nmap-notxml-1

4. Create a pull request on GitHub.


# Longer version #

5. You can also add a file indicating how the program's output should be parsed in this format: `functests/cases/out-<programname>-<desc>.yml`

# Even longer version #

6. You can add a plugin to make `ppo` behave how you'd like.  Look at `ppo/parse_plugins/nmap.py` for an example.

7. Make sure the tests pass:

    tox
