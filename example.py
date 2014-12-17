import coco.internals
import conf

class Bot(coco.internals.Manager):
	def _p_onJoin(self,group,user):pass
	def _p_onModAdded(self, group, mod):pass
	def _p_onModRemove(self, group, mod):pass
	def _p_onBannedWords(self, group, bannedwords):pass
	def _p_onMessageDelete(self,group, user, msg):pass
	def _p_onUserCount(self, group, count):pass
	def _p_onUnban(self, group, unbanned, mod):pass
	def _p_onBan(self, group, banned, mod):pass
	def _p_onStop(self):
	def _on_Message(self, group, user, msg):
		post = msg.post
		ret = "%s: %s: %s" % (group.name, user, post)
                print(ret)
bot = Bot(conf.groups, conf.name, conf.password).run()
