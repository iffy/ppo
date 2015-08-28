
If you'd like `ppo` to be able to parse the output of a program:

# Short version #

Clone this repo:

    git clone git@github.com:iffy/ppo.git

Create a branch

    git branch mybranch

Add some example output from the program in the format `functests/cases/in-<programname>-<desc>`:

    nmap -sP > functests/cases/in-nmap-notxml-1

Create a pull request on GitHub.


# If you have time #

You can also add a YAML file indicating how the program's output should be parsed in this format: `functests/cases/out-<programname>-<desc>.yml`

# If you have even more time #

You can add a plugin to make `ppo` behave how you'd like.  Look at `ppo/parse_plugins/nmap.py` for an example.

Make sure the tests pass:

    tox
