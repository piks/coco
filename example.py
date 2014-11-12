import coco.internals
import conf


class Bot(coco.internals.Manager):

	def _on_Message(self, group, user, post):
		ret = "%s: %s: %s" % (group.name, user, post)
		print(ret)

bot = Bot(conf.groups, conf.name, conf.password).run()
