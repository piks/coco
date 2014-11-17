import coco.internals
import conf


class Bot(coco.internals.Manager):
	def _p_ok(self, group):
		group.setNameColor("ff0")
		group.setFontColor("3bf")
		print("Connected to "+group.name)
	def _init(self):
		self.run()

	def _on_Message(self, group, user, msg):
		post = msg.post
		ret = "%s: %s: %s" % (group.name, user, post)
		print(ret)

bot = Bot(conf.groups, conf.name, conf.password)._init()
