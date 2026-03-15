import { useState } from "react";
import { motion } from "framer-motion";
import { ImageLightbox } from "./primitives";

export function CameraRenderer({ data }: { data: Record<string, unknown> }) {
  const res = (data.resolution ?? {}) as Record<string, number>;
  const captured = data.status === "captured";
  const imageUrl = typeof data.image_url === "string" ? data.image_url : null;
  const [lightboxOpen, setLightboxOpen] = useState(false);

  return (
    <div className="flex items-start gap-4">
      <div className="relative shrink-0 rounded-lg border border-zinc-700/60 bg-zinc-900/80 overflow-hidden">
        {imageUrl ? (
          <button type="button" onClick={() => setLightboxOpen(true)} className="cursor-pointer">
            <img
              src={imageUrl}
              alt="Microscopy capture"
              className="h-20 w-24 object-cover hover:brightness-110 transition-all"
            />
          </button>
        ) : (
          <div className="relative flex h-20 w-24 items-center justify-center">
            <svg className="absolute inset-0 h-full w-full text-zinc-600/40" viewBox="0 0 96 80">
              <path d="M2 16V4a2 2 0 012-2h12" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <path d="M82 2h12a2 2 0 012 2v12" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <path d="M94 64v12a2 2 0 01-2 2H82" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <path d="M14 78H4a2 2 0 01-2-2V64" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <line x1="44" y1="40" x2="52" y2="40" stroke="currentColor" strokeWidth="0.5" opacity="0.4" />
              <line x1="48" y1="36" x2="48" y2="44" stroke="currentColor" strokeWidth="0.5" opacity="0.4" />
            </svg>
            <span className="text-xl relative z-10">📷</span>
          </div>
        )}
        {captured && (
          <motion.div
            initial={{ top: 0 }}
            animate={{ top: "100%" }}
            transition={{ duration: 1.2, ease: "easeInOut" }}
            className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-pink-400/60 to-transparent"
          />
        )}
      </div>

      <div className="space-y-2 min-w-0">
        <div className="flex items-center gap-2.5">
          {captured && (
            <span className="inline-flex items-center rounded-md px-2.5 py-1 text-[13px] font-bold uppercase tracking-wider
                             bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Captured
            </span>
          )}
          <span className="font-mono text-[14px] text-zinc-500 truncate">{String(data.image_id ?? "—")}</span>
        </div>
        <div className="flex gap-4 text-[14px] text-zinc-500">
          <span>{String(data.camera_id ?? "zebra")}</span>
          {res.width != null && <span>{String(res.width)} × {String(res.height)}</span>}
          {data.format != null && <span>{String(data.format)}</span>}
        </div>
      </div>

      {imageUrl && (
        <ImageLightbox
          src={imageUrl}
          alt="Microscopy capture"
          open={lightboxOpen}
          onClose={() => setLightboxOpen(false)}
        />
      )}
    </div>
  );
}
