import type { Metadata } from "next";
import { Newsreader, Archivo, Space_Mono } from "next/font/google";
import "./globals.css";

const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  style: ["normal", "italic"],
  weight: ["500", "600", "700"],
});

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
});

const spaceMono = Space_Mono({
  variable: "--font-space-mono",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: "Contract Intelligence Assistant",
  description: "Ask questions about contracts and get cited answers",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${newsreader.variable} ${archivo.variable} ${spaceMono.variable} h-full antialiased`}
    >
      <body className="h-full overflow-hidden bg-background text-ink font-body">{children}</body>
    </html>
  );
}
