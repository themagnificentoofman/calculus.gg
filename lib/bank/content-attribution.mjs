// Attribution accompanies adapted expressions in immutable question snapshots.
export function contentAttribution(problem){
 const p=problem.provenance;if(p?.kind!=='adapted')return undefined;
 const values={credit:p.attribution,sourceUrl:p.sourceUrl,sourceItem:p.sourceItem||p.sourceItemLocator,license:p.license,licenseUrl:p.licenseUrl,modifications:p.modificationNotice};
 if(Object.values(values).some(v=>typeof v!=='string'||!v.trim()||v.length>6000)||!/^https:\/\//.test(values.sourceUrl)||values.license!=='CC-BY-SA-4.0'||values.licenseUrl!=='https://creativecommons.org/licenses/by-sa/4.0/')throw Error('Incomplete adapted-content attribution');
 return values;
}
