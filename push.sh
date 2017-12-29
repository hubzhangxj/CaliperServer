#!/bin/bash
#sshpass -p zuzhewaner123! rsync -avz --exclude-from='exclude.list' -e ssh -r ../CaliperServer root@106.12.27.16:/home/ts
#sshpass -p zuzhewaner123! ssh root@106.12.27.16 'chown -R www-data /home/ts/CaliperServer'
#sshpass -p zuzhewaner123! ssh root@106.12.27.16 'service apache2 restart'

#rsync -avz --exclude-from='exclude.list' -e 'ssh -p 222' -r ../Estuary litao@htsat.vicp.cc:/home/litao
#rsync -avz --exclude-from='exclude.list' -e ssh -r ../Estuary root@192.168.100.204:/root

#echo '123' | sudo -S apt-get update



sshpass -p tzy@123 rsync -avz --exclude-from='exclude.list'  -e ssh -r ../CaliperServer root@114.119.11.94:/home/ts
sshpass -p tzy@123 ssh root@114.119.11.94  'chown -R www-data /home/ts/CaliperServer'
sshpass -p tzy@123 ssh root@114.119.11.94 'service apache2 restart'