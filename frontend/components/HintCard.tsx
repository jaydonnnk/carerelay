"use client";
import { useEffect, useRef, type ReactNode, type RefObject } from "react";

/** Data exists only after the server commits Show. Native dialog supplies inertness. */
export function HintCard({ visible, revision, title, closeLabel, children, opener, fallback, onHide }: {
  visible: boolean; revision: number; title: string; closeLabel: string; children: ReactNode;
  opener: RefObject<HTMLButtonElement | null>; fallback: RefObject<HTMLElement | null>; onHide: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const node = dialog.current;
    if (visible && node && !node.open) { node.showModal(); closeButton.current?.focus(); }
    if (!visible && node?.open) node.close();
  }, [visible, revision]);
  function close() {
    dialog.current?.close();
    const target = opener.current?.isConnected ? opener.current : fallback.current;
    target?.focus();
    onHide();
  }
  if (!visible) return null;
  return <dialog className="plan-dialog" aria-labelledby="plan-dialog-title" ref={dialog}
    onCancel={event => { event.preventDefault(); close(); }}>
    <h2 id="plan-dialog-title">{title}</h2>
    {children}
    <button className="control" type="button" ref={closeButton} onClick={close}>{closeLabel}</button>
  </dialog>;
}
