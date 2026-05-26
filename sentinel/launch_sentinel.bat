@echo off
title Sentinel — Security Dashboard
cd /d "C:\Users\jerem\OneDrive\Desktop\Agentive Workflows"
cls
echo.
echo  ==============================================
echo       SENTINEL  -  Security Dashboard
echo  ==============================================
echo.
echo  Starting server on http://localhost:8502 ...
echo  Your browser will open automatically.
echo.
echo  Keep this window open while using Sentinel.
echo  Press Ctrl+C to stop the server.
echo  ==============================================
echo.
"C:\Users\jerem\AppData\Local\Programs\Python\Python314\python.exe" -m streamlit run sentinel\app.py --server.port 8502
