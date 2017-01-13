import inspect

class BaseSignal:
	_registry_list = []

	@classmethod
	def register(cls, to_register, soft=False):
		if inspect.iscoroutine(to_register):
			cls._registry_list.append([to_register, soft])


	@classmethod
	async def _run(cls, host_class):
		for i in cls._registry_list:
			try:
				await i[0](host_class)
			except Exception as e:
				if not i[1]:
					raise e
		raise Warning("Do not call it directly!!")

class ServiceReady(BaseSignal):
	pass