"use server";

/**
 * Server actions. The token stays on the server because these run on the server
 * and only their results cross the network boundary.
 *
 * A client component calling `fetch` to the API directly would need the token in
 * the browser. It does not, because of this file.
 */

import { recordHintEvent } from "@/lib/api";
import { revalidatePath } from "next/cache";

export async function showCard(episodeId: string) {
  const result = await recordHintEvent(episodeId, "H2", "shown");
  revalidatePath("/");
  return result;
}

export async function hideCard(episodeId: string) {
  const result = await recordHintEvent(episodeId, "H2", "patient_hid");
  revalidatePath("/");
  return result;
}
