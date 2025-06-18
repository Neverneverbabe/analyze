import { CustomFiles } from "@/lib/types";

export const maxDuration = 60;

export async function POST(req: Request) {
  const formData = await req.formData();
  const code = formData.get("code") as string;

  const files: CustomFiles[] = [];
  for (const [key, value] of formData.entries()) {
    if (key === "code") continue;

    if (value instanceof File) {
      const content = await value.text();
      files.push({
        name: value.name,
        content: content,
        contentType: value.type,
      });
    }
  }

  const baseURL = process.env.OPENWEBUI_BASE_URL || "http://localhost:3000";
  const apiKey = process.env.OPENWEBUI_API_KEY;
  const model = process.env.OLLAMA_MODEL || "llama3";

  const response = await fetch(`${baseURL}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: "system", content: "You are a python interpreter." },
        { role: "user", content: code },
      ],
      stream: false,
    }),
  });

  const result = await response.json();

  return new Response(JSON.stringify(result));
}
