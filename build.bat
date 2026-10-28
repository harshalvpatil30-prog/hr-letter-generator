@echo off
call venv\Scripts\activate
rmdir /s /q build dist
pyinstaller --noconfirm --name HRLetterGenerator --collect-all tkcalendar --collect-all babel --collect-all pyhanko --collect-all pyhanko_certvalidator --collect-all googleapiclient gui.py
xcopy /E /I /Y assets dist\HRLetterGenerator\assets
copy /Y credentials.json dist\HRLetterGenerator\
echo.
echo Build finished.
pause