import type { Candidate } from "@/lib/api";

type CandidatesPanelProps = {
  candidates: Candidate[];
};

const statusClass: Record<string, string> = {
  proposed: "bg-blue-50 text-blue-700 border-blue-200",
  selected: "bg-green-50 text-green-700 border-green-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
};

export function CandidatesPanel({ candidates }: CandidatesPanelProps) {
  return (
    <section className="bg-white rounded-xl border border-zinc-200 shadow-sm p-6 text-sm">
      <div className="mb-4 font-semibold tracking-tight text-zinc-900">Candidates</div>
      {candidates.length === 0 ? (
        <p className="text-zinc-500">No candidates yet. Run a scan above.</p>
      ) : (
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-zinc-100 text-zinc-500">
              <th className="pb-2 font-medium">Ticker</th>
              <th className="pb-2 font-medium">Score</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 font-medium">Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-50">
            {candidates.map((c) => (
              <tr key={c.id} className="hover:bg-zinc-50">
                <td className="py-2 font-medium">{c.ticker}</td>
                <td className="py-2 text-zinc-600">{c.score.toFixed(2)}</td>
                <td className="py-2">
                  <span className={`rounded border px-2 py-0.5 text-xs ${statusClass[c.status] ?? ""}`}>{c.status}</span>
                </td>
                <td className="py-2 text-zinc-500">{c.reason_code ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
