
rmdir /S /Q harness\player1
xcopy /I src harness\player1
echo python bots\%1\main.py %%1 > harness\player1\run.bat
 
rmdir /S /Q harness\player2
xcopy /I src harness\player2
echo python bots\%2\main.py %%1 > harness\player2\run.bat

cd harness
SpaceInvadersDuel
cd ..