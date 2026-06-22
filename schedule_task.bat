@echo off
echo Registering Windows Task Scheduler job: FARE MATRIX (daily at 7am)...

schtasks /create /tn "FARE MATRIX" ^
  /tr "\"%~dp0run.bat\"" ^
  /sc daily ^
  /st 07:00 ^
  /ru "%USERNAME%" ^
  /f

echo.
echo Done. FARE MATRIX will run every day at 7:00 AM.
echo To change to hourly, edit the task in Task Scheduler and set /sc hourly.
echo To run immediately: schtasks /run /tn "FARE MATRIX"
pause
