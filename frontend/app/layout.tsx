import type { Metadata } from "next";
import { Atkinson_Hyperlegible_Mono, Atkinson_Hyperlegible_Next } from "next/font/google";
import "./globals.css";

// Slice 22: Atkinson Hyperlegible, drawn for low-vision readers. `next/font` downloads it at
// build time and serves it from this app, so the browser makes no third-party font request.
const sans = Atkinson_Hyperlegible_Next({ subsets: ["latin"], weight: ["400", "600", "700", "800"], variable: "--font-sans", display: "swap", adjustFontFallback: false });
const mono = Atkinson_Hyperlegible_Mono({ subsets: ["latin"], weight: ["400", "600"], variable: "--font-mono", display: "swap", adjustFontFallback: false });

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
