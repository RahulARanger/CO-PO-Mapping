@echo off

REM Some commands need to be hidden but some doesn't need to

POWERSHELL -ExecutionPolicy Bypass -File "./gate.ps1" %*

@echo on