import coco.internals
import conf


class Bot(coco.internals.Manager):

	def _init(self):
		self.setNameColor("#ff0")
		self.setFontColor("#3bf")
		self.run()

	def _on_Message(self, group, user, msg):
		post = msg.post
		ret = "%s: %s: %s" % (group.name, user, post)
		print(ret)

bot = Bot(conf.groups, conf.name, conf.password)._init()
