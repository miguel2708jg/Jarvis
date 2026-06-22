import React, { useEffect, useRef, useState } from "react";
import { StyleProp, Text, TextStyle } from "react-native";

interface Props {
  text: string;
  style?: StyleProp<TextStyle>;
}

export default function StreamingText({ text, style }: Props) {
  const [cursor, setCursor] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => setCursor((current) => !current), 500);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return (
    <Text style={style}>
      {text}
      {cursor ? "|" : " "}
    </Text>
  );
}
