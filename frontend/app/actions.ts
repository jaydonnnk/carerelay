"use server";
import { cookies, headers } from "next/headers";
import { createCommand, selectExampleCommand } from "@/lib/api";
import { allowAction, LOCATOR_COOKIE } from "@/lib/episode-locator";
import type { Journey } from "@/lib/journey";

export type ActionResult = { state: "loaded"; journey: Journey } | { state: "recovery" };
async function submit(form: FormData, kind: "create" | "select_example"): Promise<ActionResult> {
  const keys = [...form.keys()].filter(k => !k.startsWith("$ACTION_"));
  const token = form.get("operation_token");
  if (keys.length !== 1 || typeof token !== "string") return { state: "recovery" };
  const h = await headers(), c = await cookies();
  const locator = allowAction(h.get("origin"), h.get("host"), c.get(LOCATOR_COOKIE)?.value,
    token, process.env.CARERELAY_API_TOKEN ?? "", kind, process.env.CARERELAY_LOOPBACK_TEST === "1");
  if (!locator) return { state: "recovery" };
  const result = kind === "create" ? await createCommand(locator.episode_id, token) : await selectExampleCommand(locator.episode_id, token);
  return result.ok ? { state: "loaded", journey: result.value.journey } : { state: "recovery" };
}
export async function startExample(_previous: ActionResult | null, form: FormData): Promise<ActionResult> {
  return submit(form, "create");
}
export async function selectExample(_previous: ActionResult | null, form: FormData): Promise<ActionResult> {
  return submit(form, "select_example");
}
