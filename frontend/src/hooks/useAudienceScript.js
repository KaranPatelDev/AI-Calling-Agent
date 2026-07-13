import { useEffect, useState } from "react";

import { api } from "../api.js";

export function useAudienceScript(setScriptText) {
  const [audience, setAudienceState] = useState("buyer");
  const [defaults, setDefaults] = useState({ buyer: "", seller: "" });

  useEffect(() => {
    api
      .getScriptSettings()
      .then((s) => {
        const next = { buyer: s.buyer_script || "", seller: s.seller_script || "" };
        setDefaults(next);
        setScriptText((prev) => prev || next.buyer);
      })
      .catch(() => {});
  }, []);

  function setAudience(value) {
    setAudienceState(value);
    setScriptText(defaults[value] || "");
  }

  return { audience, setAudience };
}
