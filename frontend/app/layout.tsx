import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Slice 22: Atkinson Hyperlegible, drawn for low-vision readers, served from this app so the
// browser makes no third-party font request. The Latin variable files are committed in
// `./fonts` (SIL Open Font License, texts alongside) instead of fetched from Google at build
// time: that fetch intermittently broke builds, locally and on Vercel.
const sans = localFont({ src: "./fonts/AtkinsonHyperlegibleNext-latin.woff2", weight: "400 800", variable: "--font-sans", display: "swap", adjustFontFallback: false });
const mono = localFont({ src: "./fonts/AtkinsonHyperlegibleMono-latin.woff2", weight: "400 600", variable: "--font-mono", display: "swap", adjustFontFallback: false });

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
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
