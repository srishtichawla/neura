import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Neura AI",
  description: "Intelligence that researches, reasons & writes",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
