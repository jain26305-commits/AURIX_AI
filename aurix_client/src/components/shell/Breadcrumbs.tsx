"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export const Breadcrumbs: React.FC = () => {
  const pathname = usePathname();
  const parts = pathname.split("/").filter(Boolean);

  return (
    <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
      <Link href="/" className="hover:text-white transition">AURIX</Link>
      {parts.map((p, idx) => (
        <React.Fragment key={p}>
          <span className="text-slate-600">/</span>
          <span className={`capitalize ${idx === parts.length - 1 ? "text-slate-300 font-semibold" : "hover:text-white"}`}>
            {p.replace(/-/g, " ")}
          </span>
        </React.Fragment>
      ))}
    </div>
  );
};
