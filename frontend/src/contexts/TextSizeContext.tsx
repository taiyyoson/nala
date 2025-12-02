import React, { createContext, useContext, useState } from "react";

type TextSize = "small" | "medium" | "large";

interface TextSizeContextProps {
  size: TextSize;
  setSize: (size: TextSize) => void;
}

const TextSizeContext = createContext<TextSizeContextProps | undefined>(undefined);

export function TextSizeProvider({ children }: { children: React.ReactNode }) {
  const [size, setSize] = useState<TextSize>("medium"); // default

  return (
    <TextSizeContext.Provider value={{ size, setSize }}>
      {children}
    </TextSizeContext.Provider>
  );
}

export function useTextSize() {
  const ctx = useContext(TextSizeContext);
  if (!ctx) throw new Error("useTextSize must be used inside TextSizeProvider");
  return ctx;
}
