rmdir /S /Q harness\player1
xcopy /I /S src harness\player1
copy src\bots\%1\bot.json harness\player1\bot.json
echo python -m ai.main %1 %%1 > harness\player1\run.bat
 
rmdir /S /Q harness\player2
xcopy /I /S src harness\player2
copy src\bots\%2\bot.json harness\player2\bot.json
echo python -m ai.main %2 %%1 > harness\player2\run.bat

cd harness
SpaceInvadersDuel
cd ..