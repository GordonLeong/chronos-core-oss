import type { Candidate } from "@/lib/api";

type CandidatesPanelProps = {
  candidates: Candidate[];
};

export function CandidatesPanel({ candidates }: CandidatesPanelProps) {
  return (
    <section className="rounded border p-3 text-sm">
      <div className="mb-2 font-semibold">Candidates</div>
      {candidates.length === 0 ? (
        <p className="text-zinc-600">No candidates yet. Run a scan.</p>
      ) : (
        <table className="w-full text-left text-xs">
          <thead>
            <tr><th>ticker</th><th>score</th><th>status</th><th>reason</th></tr>
          </thead>
          <tbody>
            {candidates.map((c) => (
              <tr key={c.id}>
                <td>{c.ticker}</td>
                <td>{c.score.toFixed(2)}</td>
                <td>{c.status}</td>
                <td>{c.reason_code ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
