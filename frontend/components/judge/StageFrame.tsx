"use client";

import { useEffect, useRef, useTransition, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { acceptFrameMessage } from "@/lib/judge";

/**
 * Slice 23 (Gate 2 D19): the unchanged patient route in a same-origin frame, beside the
 * server-rendered panel. The frame document is the patient page itself; no ledger value
 * enters it. A refresh signal from the frame re-renders the panel on the server, and the
 * visible Refresh control covers a lost message.
 */
export function StageFrame({ children }: { children: ReactNode }) {
  const frame = useRef<HTMLIFrameElement>(null);
  const router = useRouter();
  const [refreshing, startRefresh] = useTransition();

  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (!acceptFrameMessage(event, window.location.origin, frame.current?.contentWindow)) return;
      startRefresh(() => router.refresh());
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [router]);

  return (
    <div className="stage">
      <div className="phone-col">
        <div className="phone">
          <iframe ref={frame} src="/" title="Patient screen" className="phone-frame" />
        </div>
        <p className="phone-caption">What Mei sees</p>
      </div>
      <div className="panel" aria-busy={refreshing}>
        <div className="panel-tools">
          <button type="button" className="text-control" onClick={() => startRefresh(() => router.refresh())}
            aria-disabled={refreshing}>Refresh</button>
        </div>
        {children}
      </div>
    </div>
  );
}
