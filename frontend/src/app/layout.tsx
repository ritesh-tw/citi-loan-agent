import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Loan Application Agent",
  description: "AI-powered loan application agent built with Google ADK and Trustwise",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-100">{children}</body>
    </html>
  );
}
