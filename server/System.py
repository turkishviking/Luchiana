"""
module contenant le necessaire de communication avec le systeme
pour recuperer des infos, ram, cpu, temp etc
"""
import os
import subprocess
import time
import threading
import builtins
import re
import Mail

def info():
	uname=os.uname()
	kernel=uname[2]
	hostname=uname[1]
	architecture=uname[4]
	memUsed=subprocess.check_output("free -m | grep buffers/cache | awk '{print $3}'", shell=True)
	memTotal=subprocess.check_output("free -m | grep Mem | awk '{print $2}'", shell=True)
	memUsed=str(memUsed.strip(),'utf-8')
	memTotal=str(memTotal.strip(),'utf-8')
	infos="kernel %s %s on %s\nMemory %sMo/%s" % (kernel,architecture,hostname,memUsed,memTotal)
	return infos

class Monitor():

    def memUsage(self):
        self.process = subprocess.Popen("ps aux|awk 'NR > 0 {s+=$4}; END {print s}'", shell=True, stdout=subprocess.PIPE,)
        self.stdout_list = self.process.communicate()[0].split(b'\n')
        return float(self.stdout_list[0])

    def cpuUsage(self):
#à corriger, ne correspond pas ni à conky ni à htop
        self.process = subprocess.Popen("ps aux|awk 'NR > 0 {s+=$3}; END {print s}'", shell=True, stdout=subprocess.PIPE,)
        self.stdout_list = self.process.communicate()[0].split(b'\n')
        return float(self.stdout_list[0])

    def checkTemp(self):
            self.process = subprocess.Popen("sensors | grep temp1 | awk '{print $2}' | sed 's/°C//g' | sed 's/+//g'",  shell=True,stdout=subprocess.PIPE,)
            self.stdout_list = self.process.communicate()[0].split(b'\n')
            t=""
            for i in range(len(self.stdout_list)):
                if len(self.stdout_list[i])>0:
                    t+=" "+str(self.stdout_list[i].decode())+"°C"
            return t

    def checkForZombie(self):
            self.process = subprocess.Popen("ps aux | grep -w Z | grep -v 'grep' | awk '{print $2}'", shell=True, stdout=subprocess.PIPE,)
            self.stdout_list = self.process.communicate()[0].split(b'\n')
            z=""
            for i in range(len(self.stdout_list)):
                if len(self.stdout_list[i])>0:
                    z+=" "+str(self.stdout_list[i].decode())
            return z
	
    def checkMail(self,addr):
        res=Mail.checkGmail()
        return res

    def updateFiledb():
        res=subprocess.check_output("sudo updatedb")

class MyMonitoringThread(threading.Thread):
    def __init__(self, nom = ''):
        threading.Thread.__init__(self)
        self.nom = nom
        self._stopevent = threading.Event( )

    def run(self):
        mon=Monitor()
        while not self._stopevent.isSet():
            used_cpu=mon.cpuUsage()
            used_mem=mon.memUsage()
            received_mail=mon.checkMail()
            if builtins.init==1:
                if used_mem > 80:
                    builtins.sendHandler.sendMsg("N","notif;Systeme;Ram utilisee a "+str(used_mem)+"%;4")
                if used_cpu > 80:
                    builtins.sendHandler.sendMsg("N","notif;Systeme;Cpu utilise a "+str(used_cpu)+"%;4")
                if received_mail > 0:
                    builtins.sendHandler.sendMsg("N","notif;Systeme;Vous avez "+received_mail+" nouveaux mails")
            self._stopevent.wait(60)
        print("le thread "+self.nom+" s'est termine proprement")

    def stop(self):
        self._stopevent.set( )

class Command():
	def __init__(self,name,command):
		self.name=name
		self.command=command
		self.result=""
		self.codeSortie=256
	def getName(self):
		return self.name
	def execute(self):
		self.process = subprocess.Popen(self.command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		self.result = self.process.communicate()[0].split(b'\n')
		self.codeSortie = self.process.returncode
		res=self.getExitCode()
		if res==0:
			builtins.sendHandler.sendMsg("N","notif;Commande;Commande "+self.name+" executee avec succes;3")
		else:
			builtins.sendHandler.sendMsg("N","notif;Commande;La commande "+self.name+" a rencontree une erreur lors de son execution;2")
	def getResult(self):
		return self.result
	def getExitCode(self):
		return self.codeSortie

def command(afaire):
	nom=""
	if re.search("^;",afaire):
		c=afaire[1:]
	else:
		c=afaire
	nom=c.split(" ")
	cmd=Command(nom[0],c)
	threadCommande=threading.Thread(None,cmd.execute,None)
	threadCommande.start()
	inf="commande en cours"
	return inf

def receiveFile():
    return "ok"

