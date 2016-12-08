@echo off
MD peer
xcopy clientThreadConfig.cfg peer\ /q  /d
xcopy peer_program.py peer\ /q /d
MD peer1
xcopy peer\*.* peer1\ /q /d
MD peer2
xcopy peer\*.* peer2\ /q /d
MD peer3
xcopy peer\*.* peer3\ /q /d
MD peer4
xcopy peer\*.* peer4\ /q /d
MD peer5
xcopy peer\*.* peer5\ /q /d
MD peer6
xcopy peer\*.* peer6\ /q /d
MD peer7
xcopy peer\*.* peer7\ /q /d
MD peer8
xcopy peer\*.* peer8\ /q /d

start python tracking_server\tracking_server.py
start python peer1\peer_program.py
start python peer2\peer_program.py
start python peer3\peer_program.py
start python peer4\peer_program.py
start python peer5\peer_program.py
start python peer6\peer_program.py
start python peer7\peer_program.py
start python peer8\peer_program.py
