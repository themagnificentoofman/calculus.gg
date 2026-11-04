"""Portable exact finite reconstruction. No admission side effects."""
import options,odd_even_addendum
MODULES={'main55':options,'odd-even3':odd_even_addendum}
def catalog():return [{'route':route,**entry}for route,module in MODULES.items()for entry in module.catalog()]
def build(route,family,index):
 if route not in MODULES:raise ValueError('Unknown finite source route')
 return MODULES[route].build(family,index)
def verify(route,record):
 if route not in MODULES:return False
 return MODULES[route].verify(record)
