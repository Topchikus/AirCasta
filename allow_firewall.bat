@echo off
chcp 65001 >nul
title DropCast - Windows Firewall Setup
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File """%~dp0allow_firewall.ps1"""'"
