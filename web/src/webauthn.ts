// Ponte entre o JSON da API (campos em base64url) e a WebAuthn API do
// navegador (que fala em ArrayBuffer). Feito à mão para não puxar dependência
// nova — equivale ao que o @simplewebauthn/browser faria.

function b64urlToBuf(s: string): ArrayBuffer {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const b64 = (s + pad).replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out.buffer;
}

function bufToB64url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = any;

export function supportsWebAuthn(): boolean {
  return typeof window !== "undefined" && !!window.PublicKeyCredential;
}

// Cadastro: opções da API → navigator.credentials.create → resposta serializada.
export async function startRegistration(options: Json): Promise<Json> {
  const publicKey: Json = {
    ...options,
    challenge: b64urlToBuf(options.challenge),
    user: { ...options.user, id: b64urlToBuf(options.user.id) },
    excludeCredentials: (options.excludeCredentials ?? []).map((c: Json) => ({
      ...c,
      id: b64urlToBuf(c.id),
    })),
  };
  const cred = (await navigator.credentials.create({ publicKey })) as PublicKeyCredential;
  const resp = cred.response as AuthenticatorAttestationResponse;
  return {
    id: cred.id,
    rawId: bufToB64url(cred.rawId),
    type: cred.type,
    response: {
      clientDataJSON: bufToB64url(resp.clientDataJSON),
      attestationObject: bufToB64url(resp.attestationObject),
    },
    clientExtensionResults: cred.getClientExtensionResults(),
    authenticatorAttachment: (cred as Json).authenticatorAttachment ?? undefined,
  };
}

// Login: opções da API → navigator.credentials.get → resposta serializada.
export async function startAuthentication(options: Json): Promise<Json> {
  const publicKey: Json = {
    ...options,
    challenge: b64urlToBuf(options.challenge),
    allowCredentials: (options.allowCredentials ?? []).map((c: Json) => ({
      ...c,
      id: b64urlToBuf(c.id),
    })),
  };
  const cred = (await navigator.credentials.get({ publicKey })) as PublicKeyCredential;
  const resp = cred.response as AuthenticatorAssertionResponse;
  return {
    id: cred.id,
    rawId: bufToB64url(cred.rawId),
    type: cred.type,
    response: {
      clientDataJSON: bufToB64url(resp.clientDataJSON),
      authenticatorData: bufToB64url(resp.authenticatorData),
      signature: bufToB64url(resp.signature),
      userHandle: resp.userHandle ? bufToB64url(resp.userHandle) : undefined,
    },
    clientExtensionResults: cred.getClientExtensionResults(),
    authenticatorAttachment: (cred as Json).authenticatorAttachment ?? undefined,
  };
}
