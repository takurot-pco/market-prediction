import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Market Prediction",
  description: "Internal Prediction Market System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
