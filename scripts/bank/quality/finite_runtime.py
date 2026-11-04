"""Explicit offline routes for portable, independently reviewed finite bundles.

Routing does not admit an item: the contract still requires the exact registry,
review source hashes, finite domain, raw reconstruction and destination hash.
"""
from pathlib import Path
from functools import lru_cache
import importlib,importlib.util
BASE=Path(__file__).resolve().parent
INTEGRATION={'integration-bessel','integration-extensions','integration-hilbert','integration-historical','integration-moments','integration-new','integration-options','integration-repairs','integration-sign'}
ODE={'ode-mv-advanced','ode-mv-difficulty','ode-mv-gap','ode-mv-hard-headroom','ode-mv-late-difficulty','ode-mv-lower','ode-mv-lower-difficulty','ode-mv-revisions'}
DIFF_LIMITS={'diff-limits-advanced','diff-limits-lower-extensions','diff-limits-lower-replacements','diff-limits-original-revisions','ode-mv-additional-options'}
INTEGRATION_ALGEBRAIC={'integration-algebraic-main55':'main55','integration-algebraic-odd-even3':'odd-even3'}
SERIES_MATHEMATICAL={'series-mathematical-domain-six':'domain-six','series-mathematical-bracket-eighty':'bracket-eighty','series-mathematical-support-seventy-six':'support-seventy-six'}
ROUTES=INTEGRATION|ODE|DIFF_LIMITS|set(INTEGRATION_ALGEBRAIC)|set(SERIES_MATHEMATICAL)|{'ode-mv-options','ode-special-options','limits-rational-options','limits-recurrence-options','ode-nonnormal-options','mv-density-classification','ode-ground-options','series-lattice-display'}
@lru_cache(None)
def load(relative):
 path=BASE/relative;name='quality_portable_'+relative.replace('/','_').replace('.','_').replace('-','_')
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def build(route,family,index):
 if route not in ROUTES or type(index)is not int:raise ValueError('Unregistered finite bundle route')
 if route in INTEGRATION:
  module=importlib.import_module('scripts.bank.quality.integration.release_runtime');raw=module.build(route,family,index);verified=module.verify(route,raw,index)
 elif route in ODE:
  module=load('ode-mv/runtime.py');raw=module.build(route,family,index);verified=module.verify(route,raw,index)
 elif route in DIFF_LIMITS:
  module=load('diff-limits/runtime.py');module.require_reviews();raw=module.build(route,family,index);verified=module.verify(route,raw,index)
 elif route in INTEGRATION_ALGEBRAIC:
  module=load('integration/algebraic_release_runtime.py');local_route=INTEGRATION_ALGEBRAIC[route];raw=module.build(local_route,family,index);verified=module.verify(local_route,raw,index)
 elif route in SERIES_MATHEMATICAL:
  module=importlib.import_module('scripts.bank.quality.series.mathematical_runtime');local_route=SERIES_MATHEMATICAL[route];raw=module.build(local_route,family,index);verified=module.verify(local_route,raw,index)
 elif route=='ode-special-options':
  module=load('ode-special/runtime.py');module.require_reviews();raw=module.build(route,family,index);verified=module.verify(route,raw,index)
 elif route in {'limits-recurrence-options','ode-nonnormal-options','mv-density-classification','ode-ground-options'}:
  module=importlib.import_module('scripts.bank.quality.late_runtime');raw=module.build(route,family,index);verified=module.verify(route,raw)
 elif route=='series-lattice-display':
  module=load('series/lattice/runtime.py');raw=module.build(family,index);verified=module.verify(raw)
 elif route=='limits-rational-options':
  module=load('limits-options/rational/repairs.py');raw=module.build(family,index);verified=module.verify(raw)
 else:
  module=load('ode-mv/options/runtime.py');raw=module.build(family,index);verified=module.verify(raw)
 if verified is not True:raise ValueError('Portable finite verification failed')
 return raw
