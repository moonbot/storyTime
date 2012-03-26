

class ObserverError(Exception):
    pass

    
class Observable(object):
    def __init__(self, value=None):
        self._value = value
        self._observers = []
        
    def get(self):
        return self._value
        
    def set(self, value):
        self._value = value
        for observer in self._observers:
            observer()
        
    def add_observer(self, observer):
        if not hasattr(observer, '__call__'):
            raise TypeError
        self._observers.append(observer)
        
        
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)