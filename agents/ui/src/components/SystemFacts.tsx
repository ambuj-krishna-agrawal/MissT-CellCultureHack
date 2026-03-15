import { motion } from "framer-motion";

const FACTS = [
  { icon: "🧫", label: "Flask", value: "1 × T75 (75 cm²)", fixed: true },
  { icon: "🧬", label: "Cell Line", value: "iPSC-fast", fixed: true },
  { icon: "💊", label: "Media", value: "Media A (RT)", fixed: true },
  { icon: "🧪", label: "Dissociation", value: "TrypLE", fixed: true },
  { icon: "⏱", label: "Doubling", value: "~16 hrs", fixed: true },
  { icon: "🤖", label: "Robot", value: "UR12e", fixed: true },
];

export default function SystemFacts() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="border-b border-zinc-800/30 bg-zinc-900/20"
    >
      <div className="mx-auto max-w-5xl flex items-center gap-1 px-5 py-2 overflow-x-auto">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-600 mr-2 whitespace-nowrap flex-shrink-0">
          System
        </span>
        {FACTS.map((fact) => (
          <div
            key={fact.label}
            className="flex items-center gap-1.5 rounded-md border border-zinc-800/40
                       bg-zinc-900/40 px-2.5 py-1.5 flex-shrink-0"
          >
            <span className="text-[13px]">{fact.icon}</span>
            <span className="text-xs text-zinc-500">{fact.label}</span>
            <span className="text-xs font-medium text-zinc-300">{fact.value}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
