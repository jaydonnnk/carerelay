import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CareRelay",
  description:
    "SIMULATED RESEARCH DEMONSTRATION - not clinical advice, not a medical device, not validated for patient use.",
};

/**
 * The layout carries no navigation, no chrome and no framing that could imply a
 * real service. Large text, one column, and nothing that moves on its own.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
