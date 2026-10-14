"use server";
import { cookies, headers } from "next/headers";
import { createCommand, selectExampleCommand, prepareWordsCommand, readbackCommand, prepareBarrierCommand, permissionCommand } from "@/lib/api";
import { allowAction, allowPreparation, confirmedWordsDigest, barrierChoiceDigest, decodeOperation, LOCATOR_COOKIE } from "@/lib/episode-locator";
import { READBACK_KINDS, PERMISSION_KINDS, type Journey } from "@/lib/journey";

export type ActionResult = { state: "loaded"; journey: Journey } | { state: "conflict"; journey: Journey } | { state: "recovery" };
async function submit(form: FormData, kind: "create" | "select_example"): Promise<ActionResult> {
  const keys = [...form.keys()].filter(k => !k.startsWith("$ACTION_"));
  const token = form.get("operation_token");
  if (keys.length !== 1 || typeof token !== "string") return { state: "recovery" };
  const h = await headers(), c = await cookies();
  const locator = allowAction(h.get("origin"), h.get("host"), c.get(LOCATOR_COOKIE)?.value,
    token, process.env.CARERELAY_API_TOKEN ?? "", kind, process.env.CARERELAY_LOOPBACK_TEST === "1");
  if (!locator) return { state: "recovery" };
  const result = kind === "create" ? await createCommand(locator.episode_id, token) : await selectExampleCommand(locator.episode_id, token);
  return result.ok ? { state: "loaded", journey: result.value.journey } :
    result.reason === "conflict" ? { state: "loaded", journey: result.journey } : { state: "recovery" };
}
export async function startExample(_previous: ActionResult | null, form: FormData): Promise<ActionResult> {
  return submit(form, "create");
}
export async function selectExample(_previous: ActionResult | null, form: FormData): Promise<ActionResult> {
  return submit(form, "select_example");
}

export async function prepareReadbackWords(form: FormData): Promise<{ ok: true; token: string } | { ok: false }> {
  const keys = [...form.keys()].filter(k => !k.startsWith("$ACTION_"));
  const text = form.get("text"), parent = form.get("parent_id");
  if (keys.length !== 2 || typeof text !== "string" || !text.trim() || Array.from(text).length > 2048 || typeof parent !== "string") return { ok: false };
  const parentId = parent || null;
  const h = await headers(), c = await cookies(), key = process.env.CARERELAY_API_TOKEN ?? "";
  const locator = allowPreparation(h.get("origin"), h.get("host"), c.get(LOCATOR_COOKIE)?.value,
    key, process.env.CARERELAY_LOOPBACK_TEST === "1");
  if (!locator) return { ok: false };
  const digest = confirmedWordsDigest(text, parentId);
  const result = await prepareWordsCommand(locator.episode_id, digest, parentId);
  if (!result.ok) return { ok: false };
  const binding = decodeOperation(result.value, key);
  if (!binding || binding.episode_id !== locator.episode_id || binding.kind !== "confirm_words" ||
      binding.body_sha256 !== digest || binding.parent_restatement_id !== parentId || binding.confirmation_id !== null) return { ok: false };
  return { ok: true, token: result.value };
}

export async function submitReadback(form: FormData): Promise<ActionResult> {
  const keys = [...form.keys()].filter(k => !k.startsWith("$ACTION_"));
  const kind = form.get("kind"), token = form.get("operation_token"), text = form.get("text"), oldId = form.get("old_operation_id");
  const selected = READBACK_KINDS.find(k => k === kind);
  if (!selected || typeof token !== "string" || keys.length !== (selected === "confirm_words" || selected === "supersede_extraction" ? 3 : 2)) return { state: "recovery" };
  if (selected === "confirm_words" && (typeof text !== "string" || !text.trim() || Array.from(text).length > 2048)) return { state: "recovery" };
  if (selected === "supersede_extraction" && typeof oldId !== "string") return { state: "recovery" };
  const h = await headers(), c = await cookies(), key = process.env.CARERELAY_API_TOKEN ?? "";
  const locator = allowAction(h.get("origin"), h.get("host"), c.get(LOCATOR_COOKIE)?.value,
    token, key, selected, process.env.CARERELAY_LOOPBACK_TEST === "1");
  const binding = decodeOperation(token, key);
  if (!locator || !binding) return { state: "recovery" };
  const result = await readbackCommand(locator.episode_id, token, selected, binding.parent_restatement_id,
    typeof text === "string" ? text : undefined, typeof oldId === "string" ? oldId : undefined);
  return result.ok ? { state: "loaded", journey: result.value.journey } :
    result.reason === "conflict" ? { state: "conflict", journey: result.journey } : { state: "recovery" };
}

export async function prepareBarrierChoice(form: FormData): Promise<{ ok: true; token: string } | { ok: false }> {
  const keys = [...form.keys()].filter(k => !k.startsWith("$ACTION_"));
  const choice = form.get("choice_id");
  if (keys.length !== 1 || keys[0] !== "choice_id" || typeof choice !== "string" ||
      !["booking", "transport", "other"].includes(choice)) return { ok: false };
  const h = await headers(), c = await cookies(), key = process.env.CARERELAY_API_TOKEN ?? "";
  const locator = allowPreparation(h.get("origin"), h.get("host"), c.get(LOCATOR_COOKIE)?.value,
    key, process.env.CARERELAY_LOOPBACK_TEST === "1");
  if (!locator) return { ok: false };
  const digest = barrierChoiceDigest(choice);
  const result = await prepareBarrierCommand(locator.episode_id, digest);
  if (!result.ok) return { ok: false };
  const binding = decodeOperation(result.value, key);
  if (!binding || binding.episode_id !== locator.episode_id || binding.kind !== "select_barrier" ||
      binding.body_sha256 !== digest || binding.parent_restatement_id !== null || binding.confirmation_id !== null) return { ok: false };
  return { ok: true, token: result.value };
}

export async function submitPermission(form: FormData): Promise<ActionResult> {
  const kind = form.get("kind"), token = form.get("operation_token"), choice = form.get("choice_id");
  const selected = PERMISSION_KINDS.find(k => k === kind);
  if (!selected || typeof token !== "string") return { state: "recovery" };
  const keys = [...form.keys()].filter(k => !k.startsWith("$ACTION_")).sort();
  const expected = ["kind", "operation_token", ...(selected === "select_barrier" ? ["choice_id"] :
    selected === "grant_share" ? ["agreed"] : [])].sort();
  if (keys.join(",") !== expected.join(",")) return { state: "recovery" };
  if (selected === "grant_share" && form.get("agreed") !== "yes") return { state: "recovery" };
  if (selected === "select_barrier" && (typeof choice !== "string" || !["booking", "transport", "other"].includes(choice))) return { state: "recovery" };
  const h = await headers(), c = await cookies(), key = process.env.CARERELAY_API_TOKEN ?? "";
  const locator = allowAction(h.get("origin"), h.get("host"), c.get(LOCATOR_COOKIE)?.value,
    token, key, selected, process.env.CARERELAY_LOOPBACK_TEST === "1");
  const binding = decodeOperation(token, key);
  if (!locator || !binding || selected === "select_barrier" &&
      (typeof choice !== "string" || binding.body_sha256 !== barrierChoiceDigest(choice))) return { state: "recovery" };
  const result = await permissionCommand(locator.episode_id, token, selected, typeof choice === "string" ? choice : undefined);
  return result.ok ? { state: "loaded", journey: result.value.journey } :
    result.reason === "conflict" ? { state: "conflict", journey: result.journey } : { state: "recovery" };
}
