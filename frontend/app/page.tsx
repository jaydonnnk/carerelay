import { cookies } from "next/headers";
import { getEpisode } from "@/lib/api";
import { decodeLocator, creationOperation, LOCATOR_COOKIE } from "@/lib/episode-locator";
import { PatientJourney } from "@/components/PatientJourney";

export const dynamic = "force-dynamic";
export default async function PatientPage({ searchParams }: {
  searchParams: Promise<{ recovery?: string }>;
}) {
  if ((await searchParams).recovery === "1") return <PatientJourney state="recovery" />;
  const cookie = (await cookies()).get(LOCATOR_COOKIE)?.value;
  if (!cookie) return <PatientJourney state="entry" />;
  const locator = decodeLocator(cookie, process.env.CARERELAY_API_TOKEN ?? "");
  if (!locator) return <PatientJourney state="recovery" />;
  const result = await getEpisode(locator.episode_id);
  // Slice 22 (F7): a valid locator whose episode does not exist yet is a start, not a failure.
  if (!result.ok && result.reason === "not_found") return <PatientJourney state="start"
    creationToken={creationOperation(locator, process.env.CARERELAY_API_TOKEN ?? "")} />;
  if (!result.ok) return <PatientJourney state="recovery" />;
  return <PatientJourney state="loaded" journey={result.value} />;
}
