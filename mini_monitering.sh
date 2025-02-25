#!/bin/bash

ARCH=$(uname -srvmo)
OS_NAMW=$(lsb_release -i | awk '{print $3}')
OS_VER=$(lsb_release -r | awk '{print $2}')
OS="$OS_NAMW $OS_VER"
PCPU=$(grep 'physical id' /proc/cpuinfo | uniq | wc -l)
VCPU=$(grep processor /proc/cpuinfo | uniq | wc -l)
RAM_TOTAL=$(free -m | grep Mem | awk '{printf("%.2fG"), $2/1024.0}')
RAM_USED=$(free -m | grep Mem | awk '{printf("%.2fG"), $3/1024.0}')
RAM_PERC=$(free -k | grep Mem | awk '{printf("%.0f"), $3 / $2 * 100}')
DISK_TOTAL=$(df -h -l --total | grep total | awk '{print $2}')
DISK_USED=$(df -h -l --total | grep total | awk '{print $3}')
DISK_PERC=$(df -k -l --total | grep total | awk '{printf("%s%%"), $5}')
CPU_LOAD=$(uptime | awk '{print $(NF-2) $(NF-1) $NF}')
LAST_BOOT=$(who -b | awk '{print($3 " " $4)}')
TCP=$(grep TCP /proc/net/sockstat | awk '{print $3}')
USER_LOG=$(who | wc -l)
Active_VNC=$( lsof -iTCP:5900-5999 -sTCP:ESTABLISHED | grep '^Xvnc' | wc -l)
Active_ssh=$( lsof -iTCP:22 -sTCP:ESTABLISHED | grep '^sshd' | wc -l)
Active_virtuoso=$(ps -eo pid,user:20,etime,cmd | grep 64bit/virtuoso | grep -v grep | wc -l)
top_process_users=$(ps -eo user:20,etime,pcpu,pmem,cmd --sort=-pcpu | head -n 5)
top_process_mem=$(ps -eo user:20,etime,pcpu,pmem,cmd --sort=-pmem | head -n 5)
#ps -eo pid,user:20,%cpu,%mem,cmd | sort -k4,4nr | head -n 5
#ps -eo pid,user:20,%cpu,%mem,cmd | sort -k3,3nr | head -n 5

printf "$ARCH,$OS,$PCPU,$VCPU,$RAM_USED/$RAM_TOTAL,$RAM_PERC,\
$DISK_USED/$DISK_TOTAL,$DISK_PERC,$CPU_LOAD,$LAST_BOOT,\
$TCP,$USER_LOG, $Active_VNC, $Active_ssh\n"

