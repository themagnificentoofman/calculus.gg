"""Portable entrypoint: catalog(), build(family_id,index), verify(record)."""
from core import catalog,build_record as build,verify
import differentiation_new
import limits_new

import differentiation_more
import limits_more

import differentiation_structural

import differentiation_extra

import differentiation_deep

import limits_agm_rate

import limits_global

import limits_analytic

import limits_spectral

import limits_deep
import limits_repairs
import limits_partitions

# Authoring-stage demotions use truthful new identifiers, retaining candidate lineage.
from core import FAMILIES
WITHDRAWN=[]
_old_agm=FAMILIES.pop('q1-limits-olympiad-AGM-invariant-limit')
WITHDRAWN.append({k:v for k,v in _old_agm.items() if k!='build'} | {'reason':'Stage07 direct-limit options permit elementary bound elimination; superseded by a distinct gap-rate task in the same related idea group.'})
_agm_prefactor=FAMILIES['q1-limits-olympiad-AGM-normalized-gap-prefactor']
_agm_prefactor['difficulty']='hard'
_agm_prefactor['editorialDisposition']='hard-options-visible-recurrence-and-bounds; no advanced credit'
for _fid in list(FAMILIES):
 if FAMILIES[_fid]["difficulty"] != "olympiad":
  _f=FAMILIES.pop(_fid);_new=_fid.replace("-olympiad-","-"+_f["difficulty"]+"-");_f["familyId"]=_new;_f["previousCandidateFamilyId"]=_fid;FAMILIES[_new]=_f
