import collections


class OrderedClassMembers(type):
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(self, name, bases, classdict):
        classdict['__ordered__'] = [key for key in classdict.keys() if  # __classcell__ passed to __new__
                                    key not in ('__module__', '__qualname__', '__classcell__')]

        for each in bases:  # add keys from base classes also
            odict = getattr(each, '__ordered__', each.__dict__)

            classdict['__ordered__'] = [key for key in odict if key not in ('__module__', '__qualname__')] + \
                                       classdict['__ordered__']

        return type.__new__(self, name, bases, classdict)
