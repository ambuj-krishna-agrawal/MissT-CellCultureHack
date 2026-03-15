export function GenericRenderer({ data }: { data: Record<string, unknown> }) {
  const str = JSON.stringify(data, null, 2);
  return (
    <pre className="overflow-auto rounded-xl border border-zinc-800/50 bg-zinc-900/40 p-4
                    font-mono text-[14px] leading-relaxed text-zinc-400 max-h-48">
      {str}
    </pre>
  );
}
