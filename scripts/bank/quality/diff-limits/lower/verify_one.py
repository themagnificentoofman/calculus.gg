"""Fresh-process mathematical reconstruction avoids helper-module name collisions."""
import sys,json
raw=json.load(sys.stdin)
if raw['familyId'].startswith('q2-repair-'):import replacements as module
elif raw['familyId'].startswith('q2-'):import generate as module
else:import old_revisions as module
assert module.verify(raw)
print(json.dumps({'verified':True}))
