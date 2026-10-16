import { redirect } from "next/navigation";

/** Slice 24 (demo A): the bare domain opens the judge start page; the patient route is /patient. */
export default function Home() {
  redirect("/demo");
}
