import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App.tsx";
import { initAppearance } from "./theme.ts";
import "./index.css";

//  Aplica tema/layout salvos antes de pintar, evitando "piscar" cor errada.
initAppearance();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
