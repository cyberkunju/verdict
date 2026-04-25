import type { Metadata } from "next";
import Link from "next/link";
import { Playfair_Display, Inter } from "next/font/google";
import "./globals.css";

const heading = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-heading",
});

const body = Inter({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "VERDICT",
  description: "Public physiological archive of historical denials",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${heading.variable} ${body.variable} min-h-screen bg-neutral-950 text-neutral-100 antialiased`}>
        <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
          <header className="mb-8 rounded-xl border border-neutral-800/80 bg-neutral-900/70 p-4 backdrop-blur">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <Link href="/" className="font-serif text-2xl tracking-wide text-neutral-100">
                VERDICT
              </Link>
              <nav className="flex items-center gap-4 text-sm text-neutral-300">
                <Link href="/archive" className="transition-colors hover:text-white">
                  Archive
                </Link>
                <Link href="/calibration" className="transition-colors hover:text-white">
                  Calibration
                </Link>
                <Link href="/minimal" className="transition-colors hover:text-white">
                  Minimal
                </Link>
                <a href="#method" className="transition-colors hover:text-white">
                  Method
                </a>
              </nav>
            </div>
          </header>
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
