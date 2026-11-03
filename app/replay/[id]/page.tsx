import {ReplayPlayer} from '@/components/ReplayPlayer';
export default async function ReplayPage({params}:{params:Promise<{id:string}>}){const {id}=await params;return <ReplayPlayer roundId={id}/>;}
