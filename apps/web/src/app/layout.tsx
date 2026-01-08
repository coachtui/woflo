import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Woflo Dispatcher",
  description: "Diesel shop scheduling and dispatch management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
