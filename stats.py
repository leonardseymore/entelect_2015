import json
import os
import subprocess
import shutil

while True:
    shutil.rmtree('harness/Replays')
    subprocess.call(['run_harness.bat', 'haywired', 'haywired'])

    with open('harness/Replays/0001/matchinfo.json', "r") as match_file:
        matchinfo = json.loads(match_file.read())

    with open("stats.csv", "a") as myfile:
        player1 = matchinfo['Players'][0]
        player2 = matchinfo['Players'][1]

        line = '%s,%s,%s,%s\n' % (matchinfo['Rounds'], matchinfo['Winner'], player1['Kills'], player2['Kills'])
        myfile.write(line)