import { useState, useRef, type KeyboardEvent } from "react";
import { motion } from "framer-motion";

interface Props {
  onSend: (query: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 160) + "px";
    }
  };

  const canSend = !disabled && value.trim().length > 0;

  return (
    <div className="border-t border-zinc-800/40 bg-[#08080d] px-4 py-3">
      <div className="mx-auto flex max-w-4xl items-end gap-2">
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            disabled={disabled}
            placeholder="Describe a cell culture protocol..."
            rows={1}
            className="w-full resize-none rounded-xl border border-zinc-800/60 bg-surface px-4 py-3 pr-12 text-[15px]
                       text-zinc-200 placeholder-zinc-600 outline-none transition-all duration-200
                       focus:border-indigo-500/30 focus:shadow-[0_0_0_3px_rgba(99,102,241,0.06)]
                       disabled:opacity-40"
          />
        </div>
        <motion.button
          whileHover={canSend ? { scale: 1.05 } : {}}
          whileTap={canSend ? { scale: 0.95 } : {}}
          onClick={submit}
          disabled={!canSend}
          className="flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-xl
                     transition-all duration-200
                     bg-indigo-600 text-white shadow-[0_0_20px_-4px_rgba(99,102,241,0.4)]
                     hover:bg-indigo-500 hover:shadow-[0_0_24px_-4px_rgba(99,102,241,0.5)]
                     disabled:bg-zinc-800 disabled:text-zinc-600 disabled:shadow-none"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
          </svg>
        </motion.button>
      </div>
    </div>
  );
}
