import Link from "next/link"
import type { Universe } from "@/lib/api";


type UniversePanelProps = {
    universes: Universe[];
    selectedId: number;
};

export function UniversePanel({ universes, selectedId }: UniversePanelProps){
    return (
        <section className="rounded border p-3 space-y-3">
            <div className="text-sm font-semibold">Universe</div>
            <div className="flex gap-2 flex-wrap">
                {universes.map((u) => (
                <Link
                     key={u.id}
                     href={`/?universe=${u.id}`}
                     className={`rounded border px-3 py-1 ${selectedId === u.id ? "bg-zinc-900 text-white": ""}`}
                >
                    {u.name}
                </Link>
                ))}
            </div>
        </section>
    );
    
}