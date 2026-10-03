"use client";

/**
 * The hint disclosure control.
 *
 * Two buttons and nothing else. The card is shown by the patient and hidden by
 * the patient; there is no timer, no countdown and no auto-hide on either side of
 * this component (constraint C8). The server refuses an `auto_hide` event
 * outright, and this component has no `setTimeout` to attempt one with.
 *
 * The buttons call server actions rather than the API directly, so the bearer
 * token never reaches this bundle.
 */

import { useState, useTransition } from "react";
import { showCard, hideCard } from "@/app/actions";

export function HintCard({
  episodeId,
  lines,
}: {
  episodeId: string;
  /**
   * H2 shows the plan card, and the plan card is the plan. The component renders
   * these lines again rather than composing any wording of its own, because
   * patient-facing text with no approved source is the defect that cost a Gate 1
   * reopen once already (`COORDINATOR_FALLBACK_TEXT`). A control label is a
   * control; clinical copy is not this file's to write.
   */
  lines: string[];
}) {
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onShow() {
    setError(null);
    startTransition(async () => {
      const result = await showCard(episodeId);
      if (result.ok) {
        setVisible(result.value.card_visible);
      } else {
        setError(result.detail);
      }
    });
  }

  function onHide() {
    setError(null);
    startTransition(async () => {
      const result = await hideCard(episodeId);
      if (result.ok) {
        setVisible(result.value.card_visible);
      } else {
        setError(result.detail);
      }
    });
  }

  return (
    <section>
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        {visible ? (
          <button className="control" onClick={onHide} disabled={pending}>
            Hide the plan
          </button>
        ) : (
          <button className="control" onClick={onShow} disabled={pending}>
            Show the plan card
          </button>
        )}
      </div>
      {visible && (
        <div className="hint-card">
          <ol className="lines">
            {lines.map((line, index) => (
              <li key={index} className="line">
                {line}
              </li>
            ))}
          </ol>
        </div>
      )}
      {error && <p className="unavailable">{error}</p>}
    </section>
  );
}
