import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "ShockTest — Do Prediction Markets Overreact?",
  description:
    "Analyzing probability shocks in prediction markets to detect systematic mean reversion.",
  icons: {
    icon: "/BrowserLogo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      data-theme="light"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col" style={{ backgroundColor: 'var(--st-bg)', color: 'var(--st-txt)' }}>
        {children}
      </body>
    </html>
  );
}
