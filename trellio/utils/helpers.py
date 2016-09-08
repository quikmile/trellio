import inspect
from concurrent.futures import ProcessPoolExecutor

def get_class_that_defined_method(meth):
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
           if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__ # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls


def unsafe_concurrent(func, *args, **kwargs):#i.e running outside event loop, very unsafe, in case data is shared
    #e.g unsafe_concurrent(json.loads, raw_json)
    with ProcessPoolExecutor(1) as executor:
        future = executor.submit(func, *args, **kwargs)
        return future.result()
