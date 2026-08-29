import React from 'react';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#030303] text-white flex flex-col justify-center items-center relative overflow-hidden p-6 select-none">
      {/* Ambient gold background glow — on-brand black/gold identity */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_60%_60%_at_50%_50%,rgba(212,175,55,0.06)_0%,rgba(212,175,55,0.02)_40%,transparent_100%)] pointer-events-none" />
      <div className="w-full max-w-md relative z-10">
        {children}
      </div>
    </div>
  );
}