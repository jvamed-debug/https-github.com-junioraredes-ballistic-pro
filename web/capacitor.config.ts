import type { CapacitorConfig } from "@capacitor/cli";

// Empacota o build do Vite (webDir) DENTRO do app nativo — os assets rodam do
// dispositivo, não é um WebView apontando para um site (o que a Apple rejeita
// pela diretriz 4.2). O app fala com a API remota pela URL absoluta embutida
// no build via VITE_API_URL (veja DEPLOY_TO_STORES.md).
const config: CapacitorConfig = {
  appId: "com.ballisticpro.app",
  appName: "Ballistic Pro",
  webDir: "dist",
  backgroundColor: "#0a0e14",
  ios: {
    contentInset: "always",
  },
  android: {
    // Permite que o app carregue os assets locais por https://localhost.
    allowMixedContent: false,
  },
};

export default config;
