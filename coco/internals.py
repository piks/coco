################################################################
# File: internals.py
# Title: Coco - Chatango library.
# Author(s): Sorch & Piks & Dynamic
# Version: 0.3(sorta stable) - c: because you're gonna need it so freaking PRAY!
# Description:
#	  -Multi event based chatango library for handling channel messages parts/joins and other stuff
##################################################################
# -*- coding: utf-8 -*-

weights = [['5', 75], ['6', 75], ['7', 75], ['8', 75], ['16', 75], ['17', 75], ['18', 75], ['9', 95], ['11', 95], ['12', 95], ['13', 95], ['14', 95], ['15', 95], ['19', 110], ['23', 110], ['24', 110], ['25', 110], ['26', 110], ['28', 104], ['29', 104], ['30', 104], ['31', 104], ['32', 104], ['33', 104], ['35', 101], ['36', 101], ['37', 101], ['38', 101], ['39', 101], ['40', 101], ['41', 101], ['42', 101], ['43', 101], ['44', 101], ['45', 101], ['46', 101], ['47', 101], ['48', 101], ['49', 101], ['50', 101], ['52', 110], ['53', 110], ['55', 110], ['57', 110], ['58', 110], ['59', 110], ['60', 110], ['61', 110], ['62', 110], ['63', 110], ['64', 110], ['65', 110], ['66', 110], ['68', 95], ['71', 116], ['72', 116], ['73', 116], ['74', 116], ['75', 116], ['76', 116], ['77', 116], ['78', 116], ['79', 116], ['80', 116], ['81', 116], ['82', 116], ['83', 116], ['84', 116]]
specials = {"de-livechat": 5, "ver-anime": 8, "watch-dragonball": 8, "narutowire": 10, "dbzepisodeorg": 10, "animelinkz": 20, "kiiiikiii": 21, "soccerjumbo": 21, "vipstand": 21, "cricket365live": 21, "pokemonepisodeorg": 22, "watchanimeonn": 22, "leeplarp": 27, "animeultimacom": 34, "rgsmotrisport": 51, "cricvid-hitcric-": 51, "tvtvanimefreak": 54, "stream2watch3": 56, "mitvcanal": 56, "sport24lt": 56, "ttvsports": 56, "eafangames": 56, "myfoxdfw": 67, "peliculas-flv": 69, "narutochatt": 70}


try:
	import queue
except ImportError:
	import Queue as queue

import socket
import time
import threading
import random
import re
import json
import requests

class CocoError(Exception):
	pass

def getServer(g):
	try:
		sn = specials[g]
	except KeyError:
		g = g.replace("_", "q")
		g = g.replace("-", "q")
		fnv = float(int(g[0:min(5, len(g))], 36))
		lnv = g[6: (6 + min(3, len(g) - 5))]
		if(lnv):
			lnv = float(int(lnv, 36))
			if(lnv <= 1000):
				lnv = 1000
		else:
			lnv = 1000
		num = (fnv % lnv) / lnv
		maxnum = sum(map(lambda x: x[1], weights))
		cumfreq = 0
		sn = 0
		for wgt in weights:
			cumfreq += float(wgt[1]) / maxnum
			if(num <= cumfreq):
				sn = int(wgt[0])
				break
	return sn

_grouptimes = {}



def getauth(name, password):
	return requests.post("http://chatango.com/login", data = {
		"user_id": name,
		"password": password,
		"storecookie": "on",
		"checkerrors": "yes"
	}).cookies["auth.chatango.com"]


PM_SERVER = "c1.chatango.com"
PM_PORT   = 5222




class PM:
	def __init__(self, n, pw):
		self._name = n
		self._password = pw
		self._evq = queue.Queue()
		self._auth = getauth(self._name, self._password)
		self._sock = self._connect()
		self._thread   = threading.Thread(target = self._main, args = ())
		self._thread.daemon = True
		self._thread.start()
		self._pinger   = threading.Thread(target = self._pinger, args = ())
		self._pinger.daemon = True
		self._pinger.start()

	def _connect(self):
		s = socket.socket()
		s.connect((PM_SERVER, PM_PORT))
		return s

	def _main(self):
		self.send("tlogin", self._auth, "10")
		while True:
			evt = self._recv()
		
	def _pinger(self):
		while True:
			time.sleep(30)
			self.send()

	def _recv(self):
		buf = b""
		while not buf.endswith(b"\0"):
			buf += self._sock.recv(1)
		#print(buf)
		#print(buf)
		return buf[:-1].rstrip(b"\r\n").decode("utf8", "ignore")

	def send(self, *args, firstCmd = False):
		self._sock.send(":".join(args).encode("utf8", "ignore") + (b"\0" if firstCmd else b"\r\n\0"))

	def sendmsg(self, who, msg):
		self.send("msg", who, msg)




class Message(object):
	def __init__(self, **kw):
		self._mid = None
		self._name = None
		self._unid = ""
		self._raw = ""
		self._group = None
		self._post = ""
		
		for attr, val in kw.items():
			if val == None:
				continue
			setattr(self, "_" + attr, val)


	def attach(self, group, mid):
		if self._mid == None:
			self._group = group
			self._id = mid
			self._group._msgs[mid] = self
			
	def detach(self):
		if self._mid != None and self._mid in self._group._msgs:
			del self._group._msgs[self._mid]
			self._mid = None
						
	def getPost(self): return self._post
	def getUser(self): return self._name
	def getGroup(self): return self._group
	
	name = property(getUser)
	post = property(getPost)
	group = property(getGroup)
	

class Struct:
	def __init__(self, **entries):
		self.__dict__.update(entries)



class Group(object):
	def __init__(self, mgr, name, username = None, password = None, type = "user"):
		self.mgr = mgr
		self.name = name
		self.type = type
		self.username = username
		self.password = password
		self.uid = self.mgr.uid
		self.sock = None
		self.history = []
		self.unum = None
		self.server = "s%d.chatango.com" % (getServer(self.name))
		
		self._firstCommand = True
		self.connected = False
		self.usingPremium = False
		self.maxReconnectAttempts = 5
		
		self._doReconnect = True
		self._doPing = True
		
		self._doReconnect = True
		
		self._sendQueue = queue.Queue()
		self._recvQueue = queue.Queue()
		
		self._recvBuffer = [] # dat buffer doe.
		
		self._nameColor = "00F7F3"
		self._fontColor = "FF0000"
		self._fontSize ="11"
		self._fontFace = "0"
		self.reconnectAttempts = 5
		self.banlist = list()
		self.users = []
		self.user = username or None
		

	def Last(self, args, mode = "user"):
		if mode == "user":
			try: return [n for n in self.history if n.name == args][-1]
			except: return False
		elif mode == "pid":
			try: return [n for n in self.history if n.pid == args][-1]
			except: return False

	def connect(self):
		try:
			self.sock = socket.socket() # Make a new socket instance.
			print("INITCONN", self.name)
			self.sock.connect((self.server, 443))
			self.connected = True
			#time.sleep(5)
		except socket.error: # sucket pls.
			self.connected = False
		
		self.pingTimer = threading.Thread(target = self._ping) # Start a thread for sending a ping every x seconds, and set it to die when `__main__` dies.
		self.pingTimer.daemon = True
		self.pingTimer.start()
		
		self.sendTimer = threading.Thread(target = self._send) # Start a thread for sending data that's queued, every 0.2 seconds.
		self.sendTimer.daemon = True
		self.sendTimer.start()
		
		self.recvTimer = threading.Thread(target = self._recv) # Start a thread for receiving data from the socket and putting the valid data in a queue, every 0.2 seconds.
		self.recvTimer.daemon = True
		self.recvTimer.start()
		
		if self.username and self.password: # If normal user.
			self.s("bauth", self.name, self.uid, self.username, self.password) # ex. bauth:examplegroup:123456789012345:usernamehere:passwordhere
		elif self.username: # If temp.
			self.s("bauth", self.name, self.uid, self.username) # ex. bauth:examplegroup:123456789012345:tempnamehere
		else: # If anon.
			self.s("bauth", self.name, self.uid, "k", "") # ex. bauth:examplegroup:123456789012345:k:
	
	def fileno(self):
		return self.sock.fileno()

	def _ping(self): # PENG PLS
		while self._doPing:
			time.sleep(20)
			self.s("")
			#self.mgr._on_Ping(self)
	
	def s(self, *args, **kwargs): # Alias for `self.send()`
		self.send(*args, **kwargs)
	
	def send(self, *data):
		data = ":".join([str(x) for x in data])
		data = data.encode("utf-8")
		if self._firstCommand:
			data += b"\x00"
			self._firstCommand = False
		else:
			data += b"\r\n\x00"
		
		self._sendQueue.put_nowait(data)

	def _send(self):
		while self.connected:
			try:
				data = self._sendQueue.get(True, 5)
				self.sock.send(data)
				time.sleep(0.2)
			except queue.Empty:
				pass
			except socket.error:
				self.sock.close()
				self.connected = False

	def _recv(self):
		while self.connected:
			try:
				_buf = b"" # Temporary buffer.
				while not _buf.endswith(b"\x00"): # Until we've gotten a complete command, loop, getting data.
					try:
						_buf += self.sock.recv(3024)
					except socket.error: # SUCKET PLS !!!1111111!!!1!!1!
						self.sock.close()
						self.connected = False
				self._recvQueue.put(_buf) # Queue the data we got.
				#time.sleep(0.2) # Sleep to avoid looping so fast we get CPU abuse.
			except queue.Full:
				pass
			except socket.error:
				self.sock.close()
				self.connected = False


	def post(self, contents):
		_censor = {
			self.mgr.password: ' http://i.imgur.com/bqJ5N8B.jpg ', # not even secure, gg.
		}
		
		for k, v in _censor.items():
			contents = contents.replace(k, v)
		
		data = ('<n{nameColor}/><f x{fontSize}{fontColor}="{fontFace}">{contents}'.format(
			nameColor = self._nameColor,
			fontSize = self._fontSize,
			fontColor = self._fontColor,
			fontFace = self._fontFace,
			contents = contents
		))

		self.s("bmsg", "t12j", data)

	def setbg(self, mode = "1"):
		if not mode in ["0", "1"]:
			return False
		if mode == "1":
			self.s("getpremium", "1")
		self.s("msgbg", mode)

	def setvr(self, mode = "1"):
		if not mode in ["0", "1"]:
			return False
		if mode == "1":
			self.s("getpremium", "1")
		self.s("msgmedia", mode)

	def setNameColor(self, color):
		self.nameColor = str(color)

	def setFontColor(self, color):
		self.fontColor = str(color)

	def setFontFace(self, face):
		self.fontFace = str(face)

	def setFontSize(self, size):
		self.fontSize = str(size)

class Manager(object):
	def __init__(self, groups, username = None, password = None):
		self.groups = []
		self.username = username
		self.password = password
		self.usePremium = True
		self.uid = str(random.randrange(10 ** 15, (10 ** 16) - 1))
		self.startTime = time.time()
		self.prefix = "@"
		self.threads = {}
		self.queue = queue.Queue()
		self.banlist = list()
		for group in groups:
			self._add(Group(self, group, self.username, self.password)) # Make the group objects from the initial group list.
		self.connected = True
		self._msgs = dict()
		self._history = list()
		self._i_log = list()
		self._mq = dict()
		
	def getroom(self , room):
		try:return [n for n in self.groups if n.name == room][-1]
		except:return False

	def _addHistory(self, msg, room):
		self.getroom(room).history.append(msg)

	def _rH(self):
		return self._history

	
		
		
	def getMessage(self, mid):
		return self._msgs.get(mid)
	
	def createMessage(self, msgid, **kw):
		if msgid not in self._msgs:
			msg = Message(msgid = msgid, **kw)
			self._msgs[msgid] = msg
		else:
			msg = self._msgs[msgid]
		return msg
		
	def Last(self, args):
		try: return [n for n in reversed(self._mq) if n.name == args][-1]
		except: return False
			
	def _callEvent(self, evt, *args):
		if hasattr(self, "_p_%s" %  evt):
			getattr(self, "_p_%s" % evt)(args)

	def _add(self, group):
		if not group in self.groups:
			self.groups.append(group)

	def getData(self, group):
		try:
			return group._recvQueue.get()
		except queue.Empty:
			pass
			
			
	def _p_onJoin(self, args):
		print("JR","%s %s" % (args[1], args[0]))
		
	def _p_onPart(self, args):
		print("PR","%s %s" % (args[1], args[0]))
		
	def _p_ok(self, args):
		print("CONN", "%s" % args)

	def setPremium(self, group):
		group.setbg()
		group.setvr()
		group.usingPremium = True

	def getUserCount(self, group):
		return len(group.users)

	def getUsers(self, group):
		return group.users

	def cleanPost(self, post):
		#print(post)
		try:
			nColor = re.search("<n(.*?)/>", post)
			fTag = re.search("<f x(.*?)>", post).group(1)
			fSize = fTag[:2]
			fFace = re.search("(.*?)=\"(.*?)\"", fTag).group(2)
			fColor = re.search(fSize+"(.*?)=\""+fFace+"\"", fTag).group(1)
		except:
			nColor = "F7F3"
			fSize = "11"
			fColor = "000"
			fFace = "0"
		post = re.sub("<(.*?)>", "", post).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&apos;", "'").replace("&amp;", "&")

		return post, nColor, fSize, fColor, fFace

	def route(self, group, cmd, args):
		if hasattr(self, "_r_%s" % (cmd)):
		#try:
			getattr(self, "_r_%s" % (cmd))(group, args)
		#except:
		#	pass
	
	##########
	# Received tagserver commands
	#
	def _r_inited(self, group, args):
		group.s("g_participants", "start")
		group.s("blocklist", "block", "", "next", "500")
		group.s("getbannedwords")
		group.s("getratelimit")
		for msg in reversed(self._i_log):
			user = msg.name
			self._addHistory(msg, group.name)

	def _r_blocklist(self, group, args):
		if args[1]: # we have the banlist :o
			banlist = ":".join(args[1:]).split(";")
			for b in banlist: # lets parse it and add it to our list :o
				params = b.split(":")
				group.banlist.append((params[0], params[1], params[2], float(params[3]), params[4]))
	
	def _r_g_participants(self, group, args):
		ul = ":".join(args[1:]).split(";")
		for u in ul:
			u = u.split(":")[:-1]
			if u[-2] != "None" and u[-1] == "None":
				group.users.append(u[-2].lower())
				
				
	def _r_participant(self, group, args):
		if len(group.users) == 0:pass
		if args[1] == "0" and not args[4] == "None": # leave
			self._callEvent("onPart", group.name, args[4])
			if args[4] in group.users:
				group.users.remove(args[4])
		if args[1] == "1" and not args[4] == "None": # join
			self._callEvent("onJoin", group.name, args[4])
			if args[4] not in group.users:
				group.users.append(args[4])
	
	def _r_ok(self, group, args):
		self._callEvent("ok", group.name)
		group.owner = args[1]
		group.mods = args[7].split(";")
		self.ip = args[6]
	
	def _r_denied(self, group, args):
		print("denied@ %s" % group.name)
		group.sock.close()
	
	def _r_n(self, group, args):
		group.usercount =  (int(args[1], 16) or 0)

	def _r_u(self, group, args):
		args = args[1:]
		temp = Struct(**self._mq)
		if hasattr(temp, args[0]):
			msg = self._mq[args[0]]
			msg.pid = args[1]
			self_mq = msg
			self._addHistory(msg, group.name)

		
	def _r_i(self, group, args):
		args = args[1:]
		mtime = float(args[0])
		name = args[1]
		puid = args[3]
		pid = args[5]
		msgid = args[5]
		rawmsg = ":".join(args[9:])
		post, nColor, fSize, fColor, fFace = self.cleanPost(rawmsg)
		msg = self.createMessage(
			msgid = msgid,
			pid = pid,
			name = name,
			puid = puid,
			group = group.name,
			post = post
			)
		self._i_log.append(msg)
	
	def _r_bw(self, group, args):
		group.bannedwords = args[2].split("%2C")
		
	def _r_delete(self, group, args):
		try:
			try:
				msg = self.getMessage(args[1])
			except:
				msg = group.Last(args[1], mode = "pid")
			ret = "%s %s %s" % (msg.group, msg.name, msg.post)
			print(ret)
		except:
			print("Msg with unknown id deleted")
		
	def _r_b(self, group, args):
		args = args[1:]
		#print(args)
		mtime = float(args[0])
		puid = args[3]
		ip = args[6]
		name = args[1]
		i = args[5]
		unid = args[4]#this
		wtfchatango = args[6]
		rawmsg = ":".join(args[9:])
		post, nColor, fSize, fColor, fFace = self.cleanPost(rawmsg)
		msg = self.createMessage(
			msgid = i,
			name = name,
			puid = puid,
			unid = unid,
			group = group.name,
			post = post
		)

		self._mq[i] = msg

		try:
			self._on_Message(group, name, post)
		except Exception as e:
			print("Handler error:", str(e))

	def _r_annc(self, group, args):
		msg = re.sub("<(.*?)>", "", ":".join(args[3:])).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&apos;", "'").replace("&amp;", "&")
		pass

	def _r_mods(self, group, args):
		group.mods = args[1:]
	#
	##########
	
	def _parse(self, group, datas): # Mr. Data, it appears we have a slight problem.
		if not datas: return
		datas = datas.split(b"\x00")
		#print(datas)
		for data in datas:
			data = data.decode("utf-8")
			data = data.split(":")
			t = threading.Thread(target = self.route, args = (group, data[0].lower().strip(), data,))
			t.daemon = True
			t.start()
	
	def makeThread(self, group):
		if isinstance(group, (list, tuple)):
			for g in group:
				if isinstance(g, Group):
					if g in self.groups:
						return False
					self.threads[group] = threading.Thread(target = self._run, args = (g,)) # lol
					self.threads[group].daemon = True
					self.threads[group].start()
					return
		elif isinstance(group, Group):
			self.threads[group] = threading.Thread(target = self._run, args = (group,))
			self.threads[group].daemon = True
			self.threads[group].start()
			return
		return False



	def leaveG(self, ga):
		gl = []
		for go in self.groups:
			gl.append(go.name)
		if ga in gl:
			group = [f for f in self.groups if f.name.lower() == ga][0]
			group.connected = False
			group.sock.close()
			del self.threads[group]
			self.groups.remove(group)
			return True
		return False
		
	def joinG(self, ga):
		gl = []
		for g in self.groups:
			gl.append(g.name)
		if not ga in gl:
			group = Group(self, ga, self.username, self.password)
			self._add(group)
			self.makeThread(group)
			group._doReconnect = True
			return True
		return False
		
		
		
	def joinAS(self, ga, n, p):
		gl = []
		for g in self.groups:
			gl.append(g)
		if not ga in gl:
			group = Group(self, ga, n, p)
			self._add(group)
			self.makeThread(group)
			group._doReconnect = True
			return True
		return False
		
		
	def PMHanlder(self, who, m): # hanlder?
		PM(self.username, self.password).sendmsg(who , m)
			
		
			
	
	def run(self):
		PM(self.username, self.password)
		for group in self.groups: # This basically starts the bot itself.
			self.makeThread(group)
		
		while self.connected: # While the bot runs in the background, flip flop and do funny shit.
			time.sleep(1)
	
	def _run(self, group):
		group.connect()
		self.setPremium(group)
		while group.connected:
			data = self.getData(group)
			self._parse(group, data)
		if group._doReconnect:
			self.reconnect(group)
	
	def reconnect(self, group):
		if group._doReconnect:
			while group.reconnectAttempts <= group.maxReconnectAttempts:
				group.connect()
				print("Attempting to reconnect to %s. (#%d(current) of #%d(maximum))" % (group.name.capitalize(), group.reconnectAttempts, group.maxReconnectAttempts))
				group.reconnectAttempts += 1
