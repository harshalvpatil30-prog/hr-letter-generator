=====================================================================
HR LETTER & CONTRACT GENERATOR
=====================================================================

A desktop application that generates digitally signed experience
letters and employment contracts as PDFs, supports bulk generation
from a CSV file, and can upload the signed PDFs to Google Drive.


---------------------------------------------------------------------
1. PROJECT OVERVIEW
---------------------------------------------------------------------
Application type : Standalone Windows desktop GUI app
                   (a Python source version is also included)

Tools & technologies
  - Python 3
  - Tkinter / ttk + tkcalendar ......... GUI and date pickers
  - ReportLab .......................... PDF generation
  - pyHanko + cryptography ............. digital signatures (PKCS#12)
  - Google Drive API v3 + OAuth 2.0 .... optional cloud upload
  - PyInstaller ........................ packaging into an .exe

Features
  - Experience letter generator (he/she/they handled automatically)
  - Employment contract generator
  - Bulk generation from a CSV file (a bad row never stops the batch)
  - Automatic reference numbers, e.g. SGC/EXP/2026-10-27/0000001
  - Branded letterhead, "Page X of Y" footer, details tables
  - Real cryptographic digital signature with a visible stamp
  - Optional upload to a Google Drive folder named "HR Letters"


---------------------------------------------------------------------
2. FOLDER CONTENTS
---------------------------------------------------------------------
HR_Letter_Generator_Submission\
  source_code\            Python source files, assets, build.bat
  HRLetterGenerator_exe\  Ready-to-run app (zipped)

Main source files
  gui.py ............... main window (letter form, bulk, contract button)
  contract_window.py ... employment contract form
  letter_engine.py ..... builds the letter and contract PDFs
  style.py ............. design: colours, header, footer, tables
  signer.py ............ digital signing
  drive_sync.py ........ Google Drive upload
  bulk.py .............. CSV batch processing
  refs.py .............. reference number counter
  config.py ............ certificate path and password
  paths.py ............. finds files next to the app or the .exe
  make_certificate.py .. creates a self-signed signing certificate


---------------------------------------------------------------------
3. SYSTEM PREREQUISITES
---------------------------------------------------------------------
Option A - Standalone app (easiest)
  - Windows 10 or 11
  - No Python needed

Option B - From source
  - Windows 10/11 (also works on Mac/Linux)
  - Python 3.10 or newer
  - Internet connection for installing packages

Configuration files
  - assets\hr_signer.p12 ... signing certificate (password is in
                             config.py). Included.
  - assets\logo.png ........ company logo (optional; skipped if absent)
  - credentials.json ....... ONLY for Google Drive upload.
                             If it is not present, leave the
                             "Upload to Google Drive" box UNTICKED.
                             Everything else works without it.


---------------------------------------------------------------------
4. RUNNING THE STANDALONE APP (no installation)
---------------------------------------------------------------------
1. Unzip HRLetterGenerator_exe.zip.
2. Open the HRLetterGenerator folder.
3. Double-click HRLetterGenerator.exe.

Keep the folder intact: the app needs the "_internal" and "assets"
folders next to the .exe.

Generated PDFs are saved in an "output" folder next to the .exe.

Windows SmartScreen or antivirus may warn about an unsigned .exe.
Click "More info" -> "Run anyway".


---------------------------------------------------------------------
5. INSTALLATION AND SETUP FROM SOURCE
---------------------------------------------------------------------
Open Command Prompt inside the source_code folder, then run:

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

Only if assets\hr_signer.p12 is missing, create a certificate:

    python make_certificate.py

(Mac/Linux: use  source venv/bin/activate  to activate. On Linux
you may also need:  sudo apt install python3-tk )


---------------------------------------------------------------------
6. RUN COMMANDS
---------------------------------------------------------------------
From source ........ python gui.py
Standalone ......... HRLetterGenerator\HRLetterGenerator.exe
Rebuild the .exe ... build.bat   (needs the venv and PyInstaller)


---------------------------------------------------------------------
7. HOW TO USE
---------------------------------------------------------------------
Single letter
  1. Fill in name, designation, department, gender and the dates.
  2. Click "Generate Letter".
  3. The signed PDF opens automatically.

Employment contract
  1. Click "New Employment Contract...".
  2. Fill in the details (CTC, probation and notice must be numbers).
  3. Click "Generate Contract".

Bulk from CSV
  1. Click "Bulk from CSV..." and choose a file such as the included
     employees.csv.
  2. Columns: name, role, department, gender, start_date, end_date,
     issue_date   (dates as DD-MM-YYYY; issue_date may be blank).
  3. A summary shows how many were created and which rows failed.
     employees.csv contains one deliberately invalid row (line 5)
     to demonstrate this.

Google Drive upload (optional)
  1. Tick "Upload to Google Drive".
  2. On the first upload a browser opens. Sign in and click Allow.
     If Google shows "hasn't verified this app", click
     Advanced -> Go to HR Letter Generator.
  3. Files go to a Drive folder named "HR Letters". Later uploads
     need no login.
  Note: the Google account must be added as a Test User in the app's
  OAuth consent screen.


---------------------------------------------------------------------
8. NOTES FOR THE EVALUATOR
---------------------------------------------------------------------
- The digital signature is real (SHA-256, RSA 2048) but uses a
  SELF-SIGNED certificate, so Adobe Reader shows "validity unknown".
  This is expected. To see a green tick, import
  assets\hr_signer.cer into Adobe's trusted certificates.
- Tamper test: edit any word in a signed PDF and reopen it in Adobe
  Reader. It reports that the document was modified after signing.
- Reference numbers are stored in counter.json next to the app and
  count up with each document.
- The app never stores a Google password. Drive access uses OAuth and
  is limited to files the app creates (drive.file scope).
- Security note: the certificate password sits in config.py, which is
  acceptable for a demo. A production deployment would prompt for it
  or use a certificate from a certifying authority.


---------------------------------------------------------------------
9. TROUBLESHOOTING
---------------------------------------------------------------------
"No module named ..."  -> the virtual environment is not active.
                          Run  venv\Scripts\activate  first.
"Invalid password or PKCS12 data"
                       -> password in config.py does not match the
                          certificate. Delete assets\hr_signer.p12
                          and run  python make_certificate.py
Drive login page says "localhost refused to connect"
                       -> keep the app running during login and do not
                          reuse old browser tabs.
Drive error about credentials.json
                       -> file missing; leave the Drive box unticked.


Google Drive link : https://drive.google.com/drive/u/0/my-drive
