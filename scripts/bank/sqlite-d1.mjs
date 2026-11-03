// D1-compatible adapter used by operator benchmarks and tests, never by gameplay.
export function sqliteD1(sql,metrics={statements:0,rows:0}){
  function prepared(statement,values=[]){return {statement,values,bind:(...v)=>prepared(statement,v),all:async()=>{metrics.statements++;const results=sql.prepare(statement).all(...values);metrics.rows+=results.length;return {results,success:true};},run:async()=>{metrics.statements++;return sql.prepare(statement).run(...values);}};}
  return {prepare:prepared,batch:async statements=>{const rows=[];for(const statement of statements)rows.push(await statement.all());return rows;}};
}
