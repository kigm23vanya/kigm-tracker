import type { Metadata } from "next";
import type { ReactNode } from "react";

import { NavBar } from "@/components/NavBar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kigm Tracker",
  description: "Student activity and performance tracker",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ru">
      <body>
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="app-shell">
          <NavBar />
          <main className="page-shell">{children}</main>
        </div>
      </body>
    </html>
  );
}
