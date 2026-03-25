import React, { useEffect, useRef, useState } from "react";
import { Text, TextStyle } from "react-native";

interface Props {
  text: string;
  style?: TextStyle;
}

/**
 * Renders text token-by-token with a blinking cursor while streaming.
 */
export default function StreamingText({ text, style }: Props) {
  const [cursor, setCursor] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => setCursor((c) => !c), 500);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <Text style={style}>
      {text}
      {cursor ? "▋" : " "}
    </Text>
  );
}
