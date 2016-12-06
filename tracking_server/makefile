prepare:
	mkdir peer3
	mkdir peer4
	mkdir peer5
	mkdir peer6
	mkdir peer7
	mkdir peer8
	mkdir peer9
	mkdir peer10
	mkdir peer11
	mkdir peer12
	mkdir peer13

	cp makefile peer1
	cp makefile peer2
	cp makefile peer3
	cp makefile peer4
	cp makefile peer5
	cp makefile peer6
	cp makefile peer7
	cp makefile peer8
	cp makefile peer9
	cp makefile peer10
	cp makefile peer11
	cp makefile peer12
	cp makefile peer13
	cp makefile tracking_server

	cp peer_program.py peer1
	cp peer_program.py peer2
	cp peer_program.py peer3
	cp peer_program.py peer4
	cp peer_program.py peer5
	cp peer_program.py peer6
	cp peer_program.py peer7
	cp peer_program.py peer8
	cp peer_program.py peer9
	cp peer_program.py peer10
	cp peer_program.py peer11
	cp peer_program.py peer12
	cp peer_program.py peer13

	cp clientThreadConfig.cfg peer1
	cp clientThreadConfig.cfg peer2
	cp clientThreadConfig.cfg peer3
	cp clientThreadConfig.cfg peer4
	cp clientThreadConfig.cfg peer5
	cp clientThreadConfig.cfg peer6
	cp clientThreadConfig.cfg peer7
	cp clientThreadConfig.cfg peer8
	cp clientThreadConfig.cfg peer9
	cp clientThreadConfig.cfg peer10
	cp clientThreadConfig.cfg peer11
	cp clientThreadConfig.cfg peer12
	cp clientThreadConfig.cfg peer13
	cp serverThreadConfig.cfg tracking_server

	cp filelist.txt peer1
	cp filelist.txt peer2
	cp filelist.txt peer3
	cp filelist.txt peer4
	cp filelist.txt peer5
	cp filelist.txt peer6
	cp filelist.txt peer7
	cp filelist.txt peer8
	cp filelist.txt peer9
	cp filelist.txt peer10
	cp filelist.txt peer11
	cp filelist.txt peer12
	cp filelist.txt peer13

updatem:
	cp makefile peer1
	cp makefile peer2
	cp makefile peer3
	cp makefile peer4
	cp makefile peer5
	cp makefile peer6
	cp makefile peer7
	cp makefile peer8
	cp makefile peer9
	cp makefile peer10
	cp makefile peer11
	cp makefile peer12
	cp makefile peer13
	cp makefile tracking_server
updatepeer:
	cp peer_program.py peer1
	cp peer_program.py peer2
	cp peer_program.py peer3
	cp peer_program.py peer4
	cp peer_program.py peer5
	cp peer_program.py peer6
	cp peer_program.py peer7
	cp peer_program.py peer8
	cp peer_program.py peer9
	cp peer_program.py peer10
	cp peer_program.py peer11
	cp peer_program.py peer12
	cp peer_program.py peer13

updatecfg:
	cp clientThreadConfig.cfg peer1
	cp clientThreadConfig.cfg peer2
	cp clientThreadConfig.cfg peer3
	cp clientThreadConfig.cfg peer4
	cp clientThreadConfig.cfg peer5
	cp clientThreadConfig.cfg peer6
	cp clientThreadConfig.cfg peer7
	cp clientThreadConfig.cfg peer8
	cp clientThreadConfig.cfg peer9
	cp clientThreadConfig.cfg peer10
	cp clientThreadConfig.cfg peer11
	cp clientThreadConfig.cfg peer12
	cp clientThreadConfig.cfg peer13
	cp serverThreadConfig.cfg tracking_server

run1:
	uxterm -e "cd peer1 && bash" &
	uxterm -e "cd peer2 && bash" &
	uxterm -e "cd tracking_server && bash" &

run2:
	uxterm -e "cd peer3 && bash" &
	uxterm -e "cd peer4 && bash" &
	uxterm -e "cd peer5 && bash" &
	uxterm -e "cd peer6 && bash" &
	uxterm -e "cd peer7 && bash" &
	uxterm -e "cd peer8 && bash" &

run3:
	uxterm -e "cd peer9 && bash" &
	uxterm -e "cd peer10 && bash" &
	uxterm -e "cd peer11 && bash" &
	uxterm -e "cd peer12 && bash" &
	uxterm -e "cd peer13 && bash" &

startserver:
	python3 tracking_server.py

startpeer: 
	python3 peer_program.py

clean: 
	rmdir peer3
	rmdir peer4
	rmdir peer5
	rmdir peer6
	rmdir peer7
	rmdir peer8
	rmdir peer9
	rmdir peer10
	rmdir peer11
	rmdir peer12
	rmdir peer13