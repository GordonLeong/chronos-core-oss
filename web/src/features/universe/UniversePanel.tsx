import Link from "next/link"
import type { Universe } from "@/lib/api";

type UniversePanelProps = {
    universes: Universe[];
    selectedId: number;
};

export function UniversePanel({ universes, selectedId }: UniversePanelProps) {
    return (
        <section className="bg-white rounded-xl border border-zinc-200 shadow-sm p-6 space-y-3">
            <div className="text-sm font-semibold tracking-tight text-zinc-900">Universe</div>
            <div className="flex gap-2 flex-wrap">
                {universes.map((u) => (
                    <Link
                        key={u.id}
                        href={`/?universe=${u.id}`}
                        className={`rounded-md border px-3 py-1 text-sm font-medium transition-colors ${selectedId === u.id
                            ? "bg-zinc-900 text-zinc-50 border-zinc-900"
                            : "bg-white text-zinc-700 border-zinc-200 hover:bg-zinc-50"
                            }`}
                    >
                        {u.name}
                    </Link>
                ))}
            </div>
        </section>
    );
}
