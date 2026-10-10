import { getEpisode, createEpisode } from "@/lib/api";
import { HintCard } from "@/components/HintCard";

/**
 * The patient screen. Four lines, a label, and one disclosure control.
 *
 * **This component authors no plan text.** Every line rendered below comes from
 * the API's patient projection. If the call fails, the screen says so and shows
 * nothing rather than filling the gap, because four confident lines that no
 * service produced is precisely the false completion this product exists to
 * prevent.
 *
 * The judge ledger is a separate page at `/ledger`, added at Slice 12. It is
 * not linked from here and it is not shown to a patient: the ledger carries
 * `dwell_seconds` and internal ids, and the two surfaces exist for two
 * different readers.
 */
export default async function PatientPage() {
  // The tracer bullet only serves an episode it has opened, so the demo episode
  // is created before it is read, and the id used is the one the service
  // returned. A hardcoded id silently rendered "could not be reached" against a
  // healthy API; see the note in `lib/api.ts`.
  const created = await createEpisode();
  if (!created.ok) {
    return (
      <main className="screen">
        <h1 className="screen-title">CareRelay</h1>
        <p className="unavailable">
          The service could not be reached, so there is no plan to show.
        </p>
        <p className="unavailable">
          Reason: {created.detail}. Nothing on this page is a plan.
        </p>
      </main>
    );
  }
  const result = await getEpisode(created.value.episode_id);

  if (!result.ok) {
    return (
      <main className="screen">
        <h1 className="screen-title">CareRelay</h1>
        <p className="unavailable">
          The service could not be reached, so there is no plan to show.
        </p>
        <p className="unavailable">
          Reason: {result.detail}. Nothing on this page is a plan.
        </p>
      </main>
    );
  }

  const projection = result.value;

  return (
    <main className="screen">
      {/* D11: the simulated label travels with the clinical data, not with page
          chrome, so it cannot be separated from the lines it qualifies. */}
      <p className="fixture-label" role="note">
        {projection.fixture_label}
      </p>
      <h1 className="screen-title">Your plan</h1>
      <ol className="lines">
        {projection.lines.map((line, index) => (
          <li key={index} className="line">
            {line}
          </li>
        ))}
      </ol>
      <HintCard episodeId={projection.episode_id} lines={projection.lines} />
    </main>
  );
}
