class Class(object):
 
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, str(self.__dict__))
